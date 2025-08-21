from os import remove
from PIL import Image
from telethon.errors import ImageProcessFailedError, PhotoCropSizeSmallError
from telethon.errors.rpcerrorlist import (
    PhotoExtInvalidError,
    UsernameOccupiedError,
    AboutTooLongError,
    FirstNameInvalidError,
    UsernameInvalidError,
    UsernameNotModifiedError,
)
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
from telethon.tl.functions.photos import (
    DeletePhotosRequest,
    GetUserPhotosRequest,
    UploadProfilePhotoRequest,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.types import (
    InputPhoto,
    MessageMediaPhoto,
    MessageEntityMentionName,
    Channel,
    User,
)

from pagermaid.config import Config
from pagermaid.enums import Message, Client
from pagermaid.listener import listener
from pagermaid.utils import lang, safe_remove
from pagermaid.utils.bot_utils import log


@listener(
    is_plugin=False,
    command="username",
    description=lang("username_des"),
    parameters="<username>",
)
async def username(context: "Message"):
    """Reconfigure your username."""
    if len(context.parameter) > 1:
        await context.edit(f"{lang('error_prefix')}{lang('arg_error')}｝")
    if len(context.parameter) == 1:
        result = context.parameter[0]
    else:
        result = ""
    try:
        await context.client(UpdateUsernameRequest(result))
    except UsernameOccupiedError:
        await context.edit(f"{lang('error_prefix')}{lang('username_exist')}")
        return
    except UsernameInvalidError:
        await context.edit(f"{lang('error_prefix')}{lang('username_vaild')}")
        return
    except UsernameNotModifiedError:
        await context.edit(f"{lang('error_prefix')}{lang('username_exist')}")
        return
    await context.edit(lang("username_set"))
    if result == "":
        await log(lang("username_cancel"))
        return
    await log(f"{lang('username_whatset')}`{result}`")


@listener(
    is_plugin=False,
    command="name",
    description=lang("name_des"),
    parameters="<first name> <last name>",
)
async def name(context: "Message"):
    """Updates your display name."""
    if len(context.parameter) == 2:
        first_name = context.parameter[0]
        last_name = context.parameter[1]
    elif len(context.parameter) == 1:
        first_name = context.parameter[0]
        last_name = " "
    else:
        await context.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        return
    try:
        await context.client(
            UpdateProfileRequest(first_name=first_name, last_name=last_name)
        )
    except FirstNameInvalidError:
        await context.edit(f"{lang('error_prefix')}{lang('name_vaild')}")
        return
    await context.edit(lang("name_set"))
    if last_name != " ":
        await log(f"{lang('name_whatset')}`{first_name} {last_name}`.")
    else:
        await log(f"{lang('name_whatset')}`{first_name}`.")


@listener(
    is_plugin=False,
    command="pfp",
    description=lang("pfp_des"),
)
async def pfp(bot: Client, context: "Message"):
    """Sets your profile picture."""
    reply = await context.get_reply_message()
    photo = None
    if not Config.SILENT:
        await context.edit(lang("pfp_process"))
    if reply:
        if reply.media:
            if isinstance(reply.media, MessageMediaPhoto):
                photo = await bot.download_media(message=reply.photo)
            elif "image" in reply.media.document.mime_type.split("/"):
                photo = await bot.download_file(reply.media.document)
            else:
                await context.edit(f"{lang('error_prefix')}{lang('pfp_e_notp')}")

    if photo:
        try:
            await bot(UploadProfilePhotoRequest(file=await bot.upload_file(photo)))
            try:
                remove(photo)
            except:
                pass
            await context.edit("头像修改成功啦 ~")
            return
        except PhotoCropSizeSmallError:
            await context.edit(f"{lang('error_prefix')}{lang('pfp_e_size')}")
        except ImageProcessFailedError:
            await context.edit(f"{lang('error_prefix')}{lang('pfp_e_img')}")
        except PhotoExtInvalidError:
            await context.edit(f"{lang('error_prefix')}{lang('pfp_e_notp')}")
    await context.edit(f"{lang('error_prefix')}{lang('pfp_e_notp')}")
    return


@listener(
    is_plugin=False,
    command="bio",
    description="设置咱的公开情报",
    parameters="<string>",
)
async def bio(bot: "Client", context: "Message"):
    """Sets your bio."""
    try:
        await bot(UpdateProfileRequest(about=context.arguments))
    except AboutTooLongError:
        await context.edit(f"{lang('error_prefix')}{lang('bio_too_lang')}")
        return
    await context.edit(lang("bio_set"))
    if context.arguments == "":
        await log(lang("bio_cancel"))
        return
    await log(f"{lang('bio_whatset')}`{context.arguments}`.")


@listener(
    is_plugin=False,
    command="rmpfp",
    description=lang("rmpfp_des"),
    parameters=f"<{lang('int')}>",
)
async def rmpfp(bot: Client, context: "Message"):
    """Removes your profile picture."""
    group = context.text[8:]
    if group == "all":
        limit = 0
    elif group.isdigit():
        limit = int(group)
    else:
        limit = 1

    pfp_list = await bot(
        GetUserPhotosRequest(user_id=context.from_id, offset=0, max_id=0, limit=limit)
    )
    input_photos = []
    for sep in pfp_list.photos:
        input_photos.append(
            InputPhoto(
                id=sep.id,
                access_hash=sep.access_hash,
                file_reference=sep.file_reference,
            )
        )
    await bot(DeletePhotosRequest(id=input_photos))
    await context.edit(f"`{lang('rmpfp_p')}{len(input_photos)} {lang('rmpfp_l')}`")


@listener(
    is_plugin=False,
    command="profile",
    description=lang("profile_des"),
    parameters="<username / id>",
)
async def profile(context: "Message"):
    """Queries profile of a user, channel, or group."""
    if not Config.SILENT:
        await context.edit(lang("profile_process"))

    target_entity = None
    
    if context.reply_to_msg_id:
        reply_message = await context.get_reply_message()
        if reply_message:
            if reply_message.fwd_from:
                if reply_message.fwd_from.from_id:
                    target_entity = await context.client.get_entity(reply_message.fwd_from.from_id)
                else:
                    await context.edit(f"{lang('error_prefix')}{lang('profile_e_hidden')}")
                    return
            else:
                target_entity = await reply_message.get_sender()
    elif context.parameter:
        user_input = context.parameter[0]
        if user_input.isnumeric() or user_input.startswith("-100"):
            try: user_input = int(user_input)
            except ValueError: pass 
        try:
            target_entity = await context.client.get_entity(user_input)
        except (TypeError, ValueError, OverflowError):
            await context.edit(f"{lang('error_prefix')}{lang('arg_error')}")
            return
    else:
        target_entity = await context.client.get_me()

    if not target_entity:
        await context.edit(f"{lang('error_prefix')}{lang('profile_e_no')}")
        return

    caption = ""
    photo_path = f"./{target_entity.id}.jpg"

    if isinstance(target_entity, User):
        try:
            full_info = await context.client(GetFullUserRequest(target_entity))
            target_user = full_info.users[0]
            target_user_full = full_info.full_user

            user_type = "Bot" if target_user.bot else lang("profile_user")
            username_system = f"@{target_user.username}" if target_user.username else lang("profile_noset")
            first_name = target_user.first_name.replace("\u2060", "") if target_user.first_name else ""
            last_name = target_user.last_name.replace("\u2060", "") if target_user.last_name else lang("profile_noset")
            biography = target_user_full.about if target_user_full.about else lang("profile_nobio")
            common_chats_count = target_user_full.common_chats_count
            verified = lang("profile_yes") if target_user.verified else lang("profile_no")
            restricted = lang("profile_yes") if target_user.restricted else lang("profile_no")
            
            caption = (
                f"**👤 {lang('profile_name')}:**\n"
                f"**{lang('profile_username')}:** {username_system}\n"
                f"**ID:** `{target_user.id}`\n"
                f"**{lang('profile_fname')}:** [{first_name}](tg://user?id={target_user.id})\n"
                f"**{lang('profile_lname')}:** {last_name}\n"
                f"**{lang('profile_bio')}:** {biography}\n"
                f"**{lang('profile_gic')}:** {common_chats_count}\n"
                f"**{lang('profile_verified')}:** {verified}\n"
                f"**{lang('profile_restricted')}:** {restricted}\n"
                f"**{lang('profile_type')}:** {user_type}\n"
            )
        except (TypeError, ValueError):
            return await context.edit(f"{lang('error_prefix')}{lang('profile_e_no')}")

    elif isinstance(target_entity, Channel):
        try:
            full_info = await context.client(GetFullChannelRequest(channel=target_entity))
            channel = full_info.chats[0]
            channel_full = full_info.full_chat

            entity_type = lang("profile_channel") if not channel.megagroup else lang("profile_group")
            username_system = f"@{channel.username}" if channel.username else lang("profile_noset")
            description = channel_full.about if channel_full.about else lang("profile_noset")
            members_count = channel_full.participants_count
            verified = lang("profile_yes") if channel.verified else lang("profile_no")
            restricted = lang("profile_yes") if channel.restricted else lang("profile_no")

            caption = (
                f"**🏢 {lang('profile_entity_info')}:**\n"
                f"**{lang('profile_username')}:** {username_system}\n"
                f"**ID:** `{channel.id}`\n"
                f"**{lang('profile_title')}:** {channel.title}\n"
                f"**{lang('profile_type')}:** {entity_type}\n"
                f"**{lang('profile_bio')}:** {description}\n"
                f"**{lang('profile_members')}:** {members_count}\n"
                f"**{lang('profile_verified')}:** {verified}\n"
                f"**{lang('profile_restricted')}:** {restricted}"
            )
        except (TypeError, ValueError):
            return await context.edit(f"{lang('error_prefix')}{lang('profile_e_no')}")

    else:
        return await context.edit(f"{lang('error_prefix')}{lang('profile_e_unsupported')}")

    downloaded_photo = None
    try:
        downloaded_photo = await context.client.download_profile_photo(
            target_entity, file=photo_path, download_big=True
        )
        if downloaded_photo:
            try:
                TARGET_WIDTH = 300
                img = Image.open(photo_path)
                if img.width > TARGET_WIDTH:
                    aspect_ratio = img.height / img.width
                    new_height = int(TARGET_WIDTH * aspect_ratio)
                    resized_img = img.resize((TARGET_WIDTH, new_height), Image.Resampling.BICUBIC)
                    resized_img.save(photo_path)
            except Exception: pass
        
        await context.client.send_file(
            context.chat_id, photo_path, caption=caption, link_preview=False,
            reply_to=context.message.reply_to_msg_id
        )
        await context.delete()
    except Exception:
        await context.edit(caption, link_preview=False)
    finally:
        if downloaded_photo:
            safe_remove(photo_path)

@listener(
    is_plugin=False,
    command="block",
    description=lang("block_des"),
    parameters="(username/uid/reply)",
)
async def block_user(context: "Message"):
    """Block an user."""
    current_chat = await context.get_chat()
    if len(context.parameter) > 1:
        await context.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        return
    if not Config.SILENT:
        await context.edit(lang("block_process"))
    user = None
    # Priority: reply > argument > current_chat
    if context.reply_to_msg_id:  # Reply to a user
        reply_message = await context.get_reply_message()
        if reply_message and reply_message.sender_id is not None:
            user = reply_message.sender_id
    if not user and len(context.parameter) == 1:  # Argument provided
        (raw_user,) = context.parameter
        if raw_user.isnumeric():
            user = int(raw_user)
        elif context.message.entities is not None:
            if isinstance(context.message.entities[0], MessageEntityMentionName):
                user = context.message.entities[0].user_id
    if not user and isinstance(current_chat, User):
        user = current_chat.id
    if not user:
        await context.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        return
    try:
        if await context.client(BlockRequest(id=user)):
            await context.edit(f"{lang('block_success')} `{user}`")
    except Exception:  # noqa
        pass
    await context.edit(f"`{user}` {lang('block_exist')}")
    if isinstance(current_chat, User) and current_chat.id == user:
        await context.delete()


@listener(
    is_plugin=False,
    command="unblock",
    description=lang("unblock_des"),
    parameters="<username/uid/reply>",
)
async def unblock_user(context: "Message"):
    """Unblock an user."""
    if len(context.parameter) > 1:
        await context.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        return
    if not Config.SILENT:
        await context.edit(lang("unblock_process"))
    user = None
    if context.reply_to_msg_id:
        reply_message = await context.get_reply_message()
        if reply_message and reply_message.sender_id is not None:
            user = reply_message.sender_id
    if not user and len(context.parameter) == 1:
        (raw_user,) = context.parameter
        if raw_user.isnumeric():
            user = int(raw_user)
        elif context.message.entities is not None:
            if isinstance(context.message.entities[0], MessageEntityMentionName):
                user = context.message.entities[0].user_id
    if not user:
        await context.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        return
    try:
        if await context.client(UnblockRequest(id=user)):
            await context.edit(f"{lang('unblock_success')} `{user}`")
    except Exception:
        pass
    await context.edit(f"`{user}` {lang('unblock_exist')}")
