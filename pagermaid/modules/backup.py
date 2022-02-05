""" Pagermaid backup and recovery plugin. """
import json
import os
import tarfile
from distutils.util import strtobool
from io import BytesIO
from traceback import format_exc

from telethon.tl.types import MessageMediaDocument

from pagermaid import config, redis_status, redis
from pagermaid.listener import listener
from pagermaid.utils import alias_command, upload_attachment, lang

pgm_backup_zip_name = "pagermaid_backup.tar.gz"


def make_tar_gz(output_filename, source_dirs: list):
    """
    压缩 tar.gz 文件
    :param output_filename: 压缩文件名
    :param source_dirs: 需要压缩的文件列表
    :return: None
    """
    with tarfile.open(output_filename, "w:gz") as tar:
        for i in source_dirs:
            tar.add(i, arcname=os.path.basename(i))


def un_tar_gz(filename, dirs):
    """
    解压 tar.gz 文件
    :param filename: 压缩文件名
    :param dirs: 解压后的存放路径
    :return: bool
    """
    try:
        t = tarfile.open(filename, "r:gz")
        t.extractall(path=dirs)
        return True
    except Exception as e:
        print(e, format_exc())
        return False


@listener(is_plugin=True, outgoing=True, command=alias_command("backup"),
          description=lang('back_des'))
async def backup(context):
    await context.edit(lang('backup_process'))

    # Remove old backup
    if os.path.exists(pgm_backup_zip_name):
        os.remove(pgm_backup_zip_name)

    # remove mp3 , they are so big !
    for i in os.listdir("data"):
        if i.find(".mp3") != -1 or i.find(".jpg") != -1 or i.find(".flac") != -1 or i.find(".ogg") != -1:
            os.remove(f"data{os.sep}{i}")

    # backup redis when available
    redis_data = {}
    if redis_status():
        for k in redis.keys():
            data_type = redis.type(k)
            if data_type == b'string':
                v = redis.get(k)
                redis_data[k.decode()] = v.decode()

        with open(f"data{os.sep}redis.json", "w", encoding='utf-8') as f:
            json.dump(redis_data, f, indent=4)

    # run backup function
    make_tar_gz(pgm_backup_zip_name, ["data", "plugins", "config.yml"])
    if strtobool(config['log']):
        await upload_attachment(pgm_backup_zip_name, int(config['log_chatid']), None)
        await context.edit(lang("backup_success_channel"))
    else:
        await context.edit(lang("backup_success"))


@listener(is_plugin=True, outgoing=True, command=alias_command("recovery"),
          description=lang('recovery_des'))
async def recovery(context):
    message = await context.get_reply_message()

    if message and message.media:  # Overwrite local backup
        if isinstance(message.media, MessageMediaDocument):
            try:
                if message.media.document.attributes[0].file_name.find(".tar.gz") != -1:  # Verify filename
                    await context.edit(lang('recovery_down'))
                    # Start download process
                    _file = BytesIO()
                    await context.client.download_file(message.media.document, _file)
                    with open(pgm_backup_zip_name, "wb") as f:
                        f.write(_file.getvalue())
                else:
                    return await context.edit(lang('recovery_file_error'))
            except Exception as e:  # noqa
                print(e, format_exc())
                return await context.edit(lang('recovery_file_error'))
        else:
            return await context.edit(lang('recovery_file_error'))

    # Extract backup files
    await context.edit(lang('recovery_process'))
    if not os.path.exists(pgm_backup_zip_name):
        return await context.edit(lang('recovery_file_not_found'))
    elif not un_tar_gz(pgm_backup_zip_name, ""):
        os.remove(pgm_backup_zip_name)
        return await context.edit(lang('recovery_file_error'))

    # Recovery redis
    if redis_status() and os.path.exists(f"data{os.sep}redis.json"):
        with open(f"data{os.sep}redis.json", "r", encoding='utf-8') as f:
            try:
                redis_data = json.load(f)
                for k, v in redis_data.items():
                    redis.set(k, v)
            except json.JSONDecodeError:
                """JSON load failed, skip redis recovery"""
            except Exception as e:  # noqa
                print(e, format_exc())

    # Cleanup
    if os.path.exists(pgm_backup_zip_name):
        os.remove(pgm_backup_zip_name)
    if os.path.exists(f"data{os.sep}redis.json"):
        os.remove(f"data{os.sep}redis.json")

    result = await context.edit(lang('recovery_success') + " " + lang('apt_reboot'))
    if redis_status():
        redis.set("restart_edit", f"{result.id}|{result.chat_id}")
    await context.client.disconnect()
