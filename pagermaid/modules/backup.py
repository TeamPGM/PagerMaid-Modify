""" Pagermaid backup and recovery plugin. """
import json
import os
import tarfile
from distutils.util import strtobool
from io import BytesIO

from pagermaid import config, redis_status, redis, silent
from pagermaid.listener import listener
from pagermaid.utils import alias_command, upload_attachment, lang
from telethon.tl.types import MessageMediaDocument


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
        print(e)
        return False


@listener(is_plugin=True, outgoing=True, command=alias_command("backup"),
          description=lang('back_des'))
async def backup(context):
    if not silent:
        await context.edit(lang('backup_process'))
    if os.path.exists("pagermaid_backup.tar.gz"):
        os.remove("pagermaid_backup.tar.gz")
    # remove mp3 , they are so big !
    for i in os.listdir("data"):
        if i.find(".mp3") != -1 or i.find(".jpg") != -1 or i.find(".flac") != -1 or i.find(".ogg") != -1:
            os.remove(f"data{os.sep}{i}")
    # backup redis
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
    make_tar_gz("pagermaid_backup.tar.gz", ["data", "plugins", "config.yml"])
    if strtobool(config['log']):
        await upload_attachment("pagermaid_backup.tar.gz", int(config['log_chatid']), None)
        await context.edit(lang("backup_success_channel"))
    else:
        await context.edit(lang("backup_success"))


@listener(is_plugin=True, outgoing=True, command=alias_command("recovery"),
          description=lang('recovery_des'))
async def recovery(context):
    message = await context.get_reply_message()
    if message and message.media:
        if isinstance(message.media, MessageMediaDocument):
            try:
                file_name = message.media.document.attributes[0].file_name
            except:
                return await context.edit(lang('recovery_file_error'))
            if file_name.find(".tar.gz") != -1:
                await context.edit(lang('recovery_down'))
            else:
                return await context.edit(lang('recovery_file_error'))
        else:
            return await context.edit(lang('recovery_file_error'))
        _file = BytesIO()
        await context.client.download_file(message.media.document, _file)
        with open("pagermaid_backup.tar.gz", "wb") as f:
            f.write(_file.getvalue())
    if not silent:
        await context.edit(lang('recovery_process'))
    if not os.path.exists("pagermaid_backup.tar.gz"):
        return await context.edit(lang('recovery_file_not_found'))
    un_tar_gz("pagermaid_backup.tar.gz", "")
    # recovery redis
    if redis_status():
        if os.path.exists(f"data{os.sep}redis.json"):
            with open(f"data{os.sep}redis.json", "r", encoding='utf-8') as f:
                redis_data = json.load(f)
            for k, v in redis_data.items():
                redis.set(k, v)
    await context.edit(lang('recovery_success'))
