"""Pagermaid backup and recovery plugin."""

import os
import sys
import tarfile
from io import BytesIO
from traceback import format_exc

from telethon.tl.types import MessageMediaDocument

from pagermaid.config import Config
from pagermaid.enums import Message
from pagermaid.listener import listener
from pagermaid.utils import lang
from pagermaid.utils.bot_utils import upload_attachment

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


@listener(
    is_plugin=False, outgoing=True, command="backup", description=lang("backup_des")
)
async def backup(message: Message):
    await message.edit(lang("backup_process"))

    # Remove old backup
    if os.path.exists(pgm_backup_zip_name):
        os.remove(pgm_backup_zip_name)

    # remove mp3 , they are so big !
    for i in os.listdir("data"):
        if (
            i.find(".mp3") != -1
            or i.find(".jpg") != -1
            or i.find(".flac") != -1
            or i.find(".ogg") != -1
        ):
            os.remove(f"data{os.sep}{i}")

    # run backup function
    make_tar_gz(pgm_backup_zip_name, ["data", "plugins"])
    if Config.LOG:
        try:
            await upload_attachment(pgm_backup_zip_name, Config.LOG_ID, None)
            await message.edit(lang("backup_success_channel"))
        except Exception:
            await message.edit(lang("backup_success"))
    else:
        await message.edit(lang("backup_success"))


@listener(
    is_plugin=False,
    outgoing=True,
    command="recovery",
    need_admin=True,
    description=lang("recovery_des"),
)
async def recovery(message: Message):
    reply = await message.get_reply_message()

    if not reply:
        return await message.edit(lang("recovery_file_error"))
    if not reply.media:
        return await message.edit(lang("recovery_file_error"))
    if not isinstance(reply.media, MessageMediaDocument):
        return await message.edit(lang("recovery_file_error"))

    try:
        if (
            ".tar.gz" not in reply.media.document.attributes[0].file_name
        ):  # Verify filename
            return await message.edit(lang("recovery_file_error"))
        await message.edit(lang("recovery_down"))
        # Start download process
        _file = BytesIO()
        await message.client.download_file(message.media.document, _file)
        with open(pgm_backup_zip_name, "wb") as f:
            f.write(_file.getvalue())
    except Exception as e:  # noqa
        print(e, format_exc())
        return await message.edit(lang("recovery_file_error"))
    # Extract backup files
    await message.edit(lang("recovery_process"))
    if not os.path.exists(pgm_backup_zip_name):
        return await message.edit(lang("recovery_file_not_found"))
    elif not un_tar_gz(pgm_backup_zip_name, ""):
        os.remove(pgm_backup_zip_name)
        return await message.edit(lang("recovery_file_error"))

    # Cleanup
    if os.path.exists(pgm_backup_zip_name):
        os.remove(pgm_backup_zip_name)

    await message.edit(lang("recovery_success") + " " + lang("apt_reboot"))
    sys.exit(0)
    return None
