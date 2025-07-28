"""Message related utilities."""

from telethon.errors import ForbiddenError, AuthKeyError
from telethon.errors.rpcerrorlist import FloodWaitError, MessageIdInvalidError
from telethon.tl.types import ChannelForbidden

from pagermaid.config import Config
from pagermaid.enums import Message
from pagermaid.listener import listener
from pagermaid.utils import lang
from pagermaid.utils.bot_utils import log


@listener(is_plugin=False, outgoing=True, command="id", description=lang("id_des"))
async def userid(context):
    """Query the UserID of the sender of the message you replied to."""
    message = await context.get_reply_message()
    text = "Message ID: `" + str(context.message.id) + "`\n\n"
    text += "**Chat**\nid:`" + str(context.chat_id) + "`\n"
    msg_from = context.chat if context.chat else (await context.get_chat())
    if context.is_private:
        try:
            text += "first_name: `" + msg_from.first_name + "`\n"
        except TypeError:
            text += "**死号**\n"
        if msg_from.last_name:
            text += "last_name: `" + msg_from.last_name + "`\n"
        if msg_from.username:
            text += "username: @" + msg_from.username + "\n"
        if msg_from.lang_code:
            text += "lang_code: `" + msg_from.lang_code + "`\n"
    if context.is_group or context.is_channel:
        text += "title: `" + msg_from.title + "`\n"
        try:
            if msg_from.username:
                text += "username: @" + msg_from.username + "\n"
        except AttributeError:
            await context.edit(lang("leave_not_group"))
            return
        text += "date: `" + str(msg_from.date) + "`\n"
    if message:
        text += (
            "\n"
            + lang("id_hint")
            + "\nMessage ID: `"
            + str(message.id)
            + "`\n\n**User**\nid: `"
            + str(message.sender_id)
            + "`"
        )
        try:
            if message.sender.bot:
                text += f"\nis_bot: {lang('id_is_bot_yes')}"
            try:
                text += "\nfirst_name: `" + message.sender.first_name + "`"
            except TypeError:
                text += f"\n**{lang('id_da')}**"
            if message.sender.last_name:
                text += "\nlast_name: `" + message.sender.last_name + "`"
            if message.sender.username:
                text += "\nusername: @" + message.sender.username
            if message.sender.lang_code:
                text += "\nlang_code: `" + message.sender.lang_code + "`"
        except AttributeError:
            pass
        if message.forward:
            if str(message.forward.chat_id).startswith("-100"):
                text += (
                    "\n\n**Forward From Channel**\nid: `"
                    + str(message.forward.chat_id)
                    + "`\ntitle: `"
                    + message.forward.chat.title
                    + "`"
                )
                if not isinstance(message.forward.chat, ChannelForbidden):
                    if message.forward.chat.username:
                        text += "\nusername: @" + message.forward.chat.username
                    text += "\nmessage_id: `" + str(message.forward.channel_post) + "`"
                    if message.forward.post_author:
                        text += "\npost_author: `" + message.forward.post_author + "`"
                    text += "\ndate: `" + str(message.forward.date) + "`"
            else:
                if message.forward.sender:
                    text += (
                        "\n\n**Forward From User**\nid: `"
                        + str(message.forward.sender_id)
                        + "`"
                    )
                    try:
                        if message.forward.sender.bot:
                            text += f"\nis_bot: {lang('id_is_bot_yes')}"
                        try:
                            text += (
                                "\nfirst_name: `"
                                + message.forward.sender.first_name
                                + "`"
                            )
                        except TypeError:
                            text += f"\n**{lang('id_da')}**"
                        if message.forward.sender.last_name:
                            text += (
                                "\nlast_name: `"
                                + message.forward.sender.last_name
                                + "`"
                            )
                        if message.forward.sender.username:
                            text += "\nusername: @" + message.forward.sender.username
                        if message.forward.sender.lang_code:
                            text += (
                                "\nlang_code: `"
                                + message.forward.sender.lang_code
                                + "`"
                            )
                    except AttributeError:
                        pass
                    text += "\ndate: `" + str(message.forward.date) + "`"
    await context.edit(text)


@listener(
    is_plugin=False,
    outgoing=True,
    command="uslog",
    description=lang("uslog_des"),
    parameters="<string>",
)
async def uslog(message: Message):
    """Forwards a message into log group"""
    if Config.LOG:
        if message.reply_to_msg_id:
            reply_msg = await message.get_reply_message()
            await reply_msg.forward_to(Config.LOG_ID)
        elif message.arguments:
            await log(message.arguments)
        else:
            await message.edit(lang("arg_error"))
            return
        await message.edit(lang("uslog_success"))
    else:
        await message.edit(lang("uslog_log_disable"))
    return


@listener(
    is_plugin=False,
    outgoing=True,
    command="log",
    description=lang("log_des"),
    parameters="<string>",
)
async def logging(message: Message):
    """Forwards a message into log group"""
    if Config.LOG:
        if message.reply_to_msg_id:
            reply_msg = await message.get_reply_message()
            await reply_msg.forward_to(Config.LOG_ID)
        elif message.arguments:
            await log(message.arguments)
        else:
            await message.edit(lang("arg_error"))
            return
        await message.delete()
    else:
        await message.edit(lang("uslog_log_disable"))


@listener(
    is_plugin=False,
    outgoing=True,
    command="re",
    description=lang("re_des"),
    parameters=lang("re_parameters"),
)
async def re(message: Message):
    """Forwards a message into this group"""
    reply = await message.get_reply_message()
    if reply:
        if message.arguments == "":
            num = 1
        else:
            try:
                num = int(message.arguments)
                if num > 100:
                    await message.edit(lang("re_too_big"))
            except Exception:
                await message.edit(lang("re_arg_error"))
                return
        await message.safe_delete()
        forward_allowed = True
        for nums in range(0, num):
            try:
                if forward_allowed:
                    await reply.forward_to(reply.peer_id)
                else:
                    await message.client.send_message(reply.peer_id, reply)
            except MessageIdInvalidError:
                if forward_allowed:
                    forward_allowed = False
                    await message.client.send_message(reply.peer_id, reply)
                else:
                    await message.respond(lang("re_forbidden"))
                    return
            except (ForbiddenError, FloodWaitError, ValueError):
                return
            except AuthKeyError:
                await message.respond(lang("re_forbidden"))
                return
    else:
        await message.edit(lang("not_reply"))
