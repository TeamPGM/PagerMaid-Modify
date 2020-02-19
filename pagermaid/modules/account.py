""" This module contains utils to configure your account. """

from os import remove
from telethon.errors import ImageProcessFailedError, PhotoCropSizeSmallError
from telethon.errors.rpcerrorlist import PhotoExtInvalidError, UsernameOccupiedError, AboutTooLongError, \
    FirstNameInvalidError, UsernameInvalidError
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
from telethon.tl.functions.photos import DeletePhotosRequest, GetUserPhotosRequest, UploadProfilePhotoRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import InputPhoto, MessageMediaPhoto, MessageEntityMentionName
from struct import error as StructError
from pagermaid import bot, log
from pagermaid.listener import listener


@listener(outgoing=True, command="username",
          description="通过命令快捷设置 username",
          parameters="<username>")
async def username(context):
    """ 重新配置您的用户名。 """
    if len(context.parameter) > 1:
        await context.edit("无效的参数。")
    if len(context.parameter) == 1:
        result = context.parameter[0]
    else:
        result = ""
    try:
        await bot(UpdateUsernameRequest(result))
    except UsernameOccupiedError:
        await context.edit("用户名已存在。")
        return
    except UsernameInvalidError:
        await context.edit("出错了呜呜呜 ~ 您好像输入了一个无效的用户名。")
        return
    await context.edit("用户名设置完毕。")
    if result == "":
        await log("用户名已被取消。")
        return
    await log(f"用户名已被设置为 `{result}`.")


@listener(outgoing=True, command="name",
          description="换个显示名称。",
          parameters="<first name> <last name>")
async def name(context):
    """ Updates your display name. """
    if len(context.parameter) == 2:
        first_name = context.parameter[0]
        last_name = context.parameter[1]
    elif len(context.parameter) == 1:
        first_name = context.parameter[0]
        last_name = " "
    else:
        await context.edit("无效的参数。")
        return
    try:
        await bot(UpdateProfileRequest(
            first_name=first_name,
            last_name=last_name))
    except FirstNameInvalidError:
        await context.edit("出错了呜呜呜 ~ 您好像输入了一个无效的 first name.")
        return
    await context.edit("显示名称已成功更改。")
    if last_name != " ":
        await log(f"显示名称已被更改为 `{first_name} {last_name}`.")
    else:
        await log(f"显示名称已被更改为 `{first_name}`.")


@listener(outgoing=True, command="pfp",
          description="回复某条带附件的消息然后把它变成咱的头像")
async def pfp(context):
    """ Sets your profile picture. """
    reply = await context.get_reply_message()
    photo = None
    await context.edit("设置头像中 . . .")
    if reply.media:
        if isinstance(reply.media, MessageMediaPhoto):
            photo = await bot.download_media(message=reply.photo)
        elif "image" in reply.media.document.mime_type.split('/'):
            photo = await bot.download_file(reply.media.document)
        else:
            await context.edit("出错了呜呜呜 ~ 无法将附件解析为图片。")

    if photo:
        try:
            await bot(UploadProfilePhotoRequest(
                await bot.upload_file(photo)
            ))
            remove(photo)
            await context.edit("头像修改成功啦 ~")
        except PhotoCropSizeSmallError:
            await context.edit("出错了呜呜呜 ~ 图像尺寸小于最小要求。")
        except ImageProcessFailedError:
            await context.edit("出错了呜呜呜 ~ 服务器解释命令时发生错误。")
        except PhotoExtInvalidError:
            await context.edit("出错了呜呜呜 ~ 无法将附件解析为图片。")


@listener(outgoing=True, command="bio",
          description="设置咱的公开情报",
          parameters="<string>")
async def bio(context):
    """ Sets your bio. """
    try:
        await bot(UpdateProfileRequest(about=context.arguments))
    except AboutTooLongError:
        await context.edit("出错了呜呜呜 ~ 情报太长啦")
        return
    await context.edit("此情报公成功啦")
    if context.arguments == "":
        await log("公开的情报成功关闭啦")
        return
    await log(f"公开的情报已被设置为 `{context.arguments}`.")


@listener(outgoing=True, command="rmpfp",
          description="删除指定数量的头像",
          parameters="<整数>")
async def rmpfp(context):
    """ Removes your profile picture. """
    group = context.text[8:]
    if group == 'all':
        limit = 0
    elif group.isdigit():
        limit = int(group)
    else:
        limit = 1

    pfp_list = await bot(GetUserPhotosRequest(
        user_id=context.from_id,
        offset=0,
        max_id=0,
        limit=limit))
    input_photos = []
    for sep in pfp_list.photos:
        input_photos.append(
            InputPhoto(
                id=sep.id,
                access_hash=sep.access_hash,
                file_reference=sep.file_reference
            )
        )
    await bot(DeletePhotosRequest(id=input_photos))
    await context.edit(f"`删除了 {len(input_photos)} 张头像。`")


@listener(outgoing=True, command="profile",
          description="生成一个用户简介 ~ 消息有点长",
          parameters="<username>")
async def profile(context):
    """ Queries profile of a user. """
    if len(context.parameter) > 1:
        await context.edit("无效的参数。")
        return

    await context.edit("正在生成用户简介摘要 . . .")
    if context.reply_to_msg_id:
        reply_message = await context.get_reply_message()
        user_id = reply_message.from_id
        target_user = await context.client(GetFullUserRequest(user_id))
    else:
        if len(context.parameter) == 1:
            user = context.parameter[0]
            if user.isnumeric():
                user = int(user)
        else:
            user_object = await context.client.get_me()
            user = user_object.id
        if context.message.entities is not None:
            if isinstance(context.message.entities[0], MessageEntityMentionName):
                return await context.client(GetFullUserRequest(context.message.entities[0].user_id))
        try:
            user_object = await context.client.get_entity(user)
            target_user = await context.client(GetFullUserRequest(user_object.id))
        except (TypeError, ValueError, OverflowError, StructError) as exception:
            if str(exception).startswith("出错了呜呜呜 ~ 找不到与之对应的任何内容"):
                await context.edit("出错了呜呜呜 ~ 指定的用户不存在。")
                return
            if str(exception).startswith("出错了呜呜呜 ~ 没有用户"):
                await context.edit("出错了呜呜呜 ~ 指定的用户名不存在。")
                return
            if str(exception).startswith("出错了呜呜呜 ~ 您确定输入了东西？") or isinstance(exception, StructError):
                await context.edit("出错了呜呜呜 ~ 指定的UserID与用户不对应。")
                return
            if isinstance(exception, OverflowError):
                await context.edit("出错了呜呜呜 ~ 指定的 UserID 已超出整数限制，您确定输对了？")
                return
            raise exception
    user_type = "Bot" if target_user.user.bot else "User"
    username_system = f"@{target_user.user.username}" if target_user.user.username is not None else (
        "This user have not yet defined their username.")
    first_name = target_user.user.first_name.replace("\u2060", "")
    last_name = target_user.user.last_name.replace("\u2060", "") if target_user.user.last_name is not None else (
        "This user did not define a last name."
    )
    biography = target_user.about if target_user.about is not None else "This user did not define a biography string."
    caption = f"**Profile:** \n" \
              f"Username: {username_system} \n" \
              f"UserID: {target_user.user.id} \n" \
              f"First Name: {first_name} \n" \
              f"Last Name: {last_name} \n" \
              f"Biography: {biography} \n" \
              f"Common Groups: {target_user.common_chats_count} \n" \
              f"Verified: {target_user.user.verified} \n" \
              f"Restricted: {target_user.user.restricted} \n" \
              f"Type: {user_type} \n" \
              f"Permanent Link: [{first_name}](tg://user?id={target_user.user.id})"
    reply_to = context.message.reply_to_msg_id
    photo = await context.client.download_profile_photo(
        target_user.user.id,
        "./" + str(target_user.user.id) + ".jpg",
        download_big=True
    )
    if not reply_to:
        reply_to = None
    try:
        await context.client.send_file(
            context.chat_id,
            photo,
            caption=caption,
            link_preview=False,
            force_document=False,
            reply_to=reply_to
        )
        if not photo.startswith("http"):
            remove(photo)
        await context.delete()
        return
    except TypeError:
        await context.edit(caption)
    remove(photo)
