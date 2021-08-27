""" Message related utilities. """

import requests
import json

from telethon.tl.functions.messages import DeleteChatUserRequest
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.errors import ForbiddenError
from telethon.errors.rpcerrorlist import ChatIdInvalidError, FloodWaitError
from distutils.util import strtobool
from pagermaid import bot, log, config, proxies
from pagermaid.listener import listener
from pagermaid.utils import lang, alias_command


@listener(is_plugin=False, outgoing=True, command=alias_command("id"),
          description=lang('id_des'))
async def userid(context):
    """ Query the UserID of the sender of the message you replied to. """
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
            await context.edit(lang('leave_not_group'))
            return
        text += "date: `" + str(msg_from.date) + "`\n"
    if message:
        text += "\n" + lang('id_hint') + "\nMessage ID: `" + str(message.id) + "`\n\n**User**\nid: `" + str(message.sender_id) + "`"
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
            if str(message.forward.chat_id).startswith('-100'):
                text += "\n\n**Forward From Channel**\nid: `" + str(
                    message.forward.chat_id) + "`\ntitle: `" + message.forward.chat.title + "`"
                if message.forward.chat.username:
                    text += "\nusername: @" + message.forward.chat.username
                text += "\nmessage_id: `" + str(message.forward.channel_post) + "`"
                if message.forward.post_author:
                    text += "\npost_author: `" + message.forward.post_author + "`"
                text += "\ndate: `" + str(message.forward.date) + "`"
            else:
                if message.forward.sender:
                    text += "\n\n**Forward From User**\nid: `" + str(
                        message.forward.sender_id) + "`"
                    try:
                        if message.forward.sender.bot:
                            text += f"\nis_bot: {lang('id_is_bot_yes')}"
                        try:
                            text += "\nfirst_name: `" + message.forward.sender.first_name + "`"
                        except TypeError:
                            text += f"\n**{lang('id_da')}**"
                        if message.forward.sender.last_name:
                            text += "\nlast_name: `" + message.forward.sender.last_name + "`"
                        if message.forward.sender.username:
                            text += "\nusername: @" + message.forward.sender.username
                        if message.forward.sender.lang_code:
                            text += "\nlang_code: `" + message.forward.sender.lang_code + "`"
                    except AttributeError:
                        pass
                    text += "\ndate: `" + str(message.forward.date) + "`"
    await context.edit(text)


@listener(is_plugin=False, outgoing=True, command=alias_command("uslog"),
          description=lang('uslog_des'),
          parameters="<string>")
async def uslog(context):
    """ Forwards a message into log group """
    if strtobool(config['log']):
        if context.reply_to_msg_id:
            reply_msg = await context.get_reply_message()
            await reply_msg.forward_to(int(config['log_chatid']))
        elif context.arguments:
            await log(context.arguments)
        else:
            await context.edit(lang('arg_error'))
            return
        await context.edit(lang('uslog_success'))
    else:
        await context.edit(lang('uslog_log_disable'))


@listener(is_plugin=False, outgoing=True, command=alias_command("log"),
          description=lang('log_des'),
          parameters="<string>")
async def logging(context):
    """ Forwards a message into log group """
    if strtobool(config['log']):
        if context.reply_to_msg_id:
            reply_msg = await context.get_reply_message()
            await reply_msg.forward_to(int(config['log_chatid']))
        elif context.arguments:
            await log(context.arguments)
        else:
            await context.edit(lang('arg_error'))
            return
        await context.delete()
    else:
        await context.edit(lang('uslog_log_disable'))


@listener(is_plugin=False, outgoing=True, command=alias_command("re"),
          description=lang('re_des'),
          parameters=lang('re_parameters'))
async def re(context):
    """ Forwards a message into this group """
    reply = await context.get_reply_message()
    if reply:
        if context.arguments == '':
            num = 1
        else:
            try:
                num = int(context.arguments)
                if num > 100:
                    await context.edit(lang('re_too_big'))
                    return True
            except:
                await context.edit(lang('re_arg_error'))
                return True
        try:
            await context.delete()
        except ValueError:
            pass
        try:
            for nums in range(0, num):
                await reply.forward_to(int(context.chat_id))
        except ForbiddenError:
            return
        except FloodWaitError:
            return
        except ValueError:
            return
    else:
        await context.edit(lang('not_reply'))


@listener(is_plugin=False, outgoing=True, command=alias_command("leave"),
          description=lang('leave_res'))
async def leave(context):
    """ It leaves you from the group. """
    if context.is_group:
        await context.edit(lang('leave_bye'))
        try:
            await bot(DeleteChatUserRequest(chat_id=context.chat_id,
                                            user_id=context.sender_id
                                            ))
        except ChatIdInvalidError:
            await bot(LeaveChannelRequest(context.chat_id))
    else:
        await context.edit(lang('leave_not_group'))


@listener(is_plugin=False, outgoing=True, command=alias_command("meter2feet"),
          description=lang('m2f_des'),
          parameters="<meters>")
async def meter2feet(context):
    """ Convert meter to feet. """
    if not len(context.parameter) == 1:
        await context.edit(lang('arg_error'))
        return
    meter = float(context.parameter[0])
    feet = meter / .3048
    await context.edit(f"{lang('m2f_get')} {str(meter)}{lang('m2f_meter')} {lang('m2f_covert_to')}  {str(feet)}{lang('m2f_feet')}")


@listener(is_plugin=False, outgoing=True, command=alias_command("feet2meter"),
          description=lang('f2m_des'),
          parameters="<feet>")
async def feet2meter(context):
    """ Convert feet to meter. """
    if not len(context.parameter) == 1:
        await context.edit(lang('arg_error'))
        return
    feet = float(context.parameter[0])
    meter = feet * .3048
    await context.edit(f"{lang('m2f_get')} {str(feet)} {lang('m2f_feet')}{lang('m2f_covert_to')} {str(meter)}{lang('m2f_meter')}")


@listener(is_plugin=False, outgoing=True, command=alias_command("hitokoto"),
          description=lang('hitokoto_des'))
async def hitokoto(context):
    """ Get hitokoto.cn """
    hitokoto_while = 1
    hitokoto_json = None
    try:
        hitokoto_json = json.loads(requests.get("https://v1.hitokoto.cn/?charset=utf-8", proxies=proxies).content.decode("utf-8"))
    except ValueError:
        while hitokoto_while < 10:
            hitokoto_while += 1
            try:
                hitokoto_json = json.loads(
                    requests.get("https://v1.hitokoto.cn/?charset=utf-8", proxies=proxies).content.decode("utf-8"))
                break
            except:
                continue
        if not hitokoto_json:
            return
    hitokoto_type = {'a': lang('hitokoto_type_anime'), 'b': lang('hitokoto_type_manga'),
                     'c': lang('hitokoto_type_game'),  'd': lang('hitokoto_type_article'),
                     'e': lang('hitokoto_type_original'), 'f': lang('hitokoto_type_web'),
                     'g': lang('hitokoto_type_other'), 'h': lang('hitokoto_type_movie'),
                     'i': lang('hitokoto_type_poem'), 'j': lang('hitokoto_type_netease_music'),
                     'k': lang('hitokoto_type_philosophy'), 'l': lang('hitokoto_type_meme')}
    await context.edit(f"{hitokoto_json['hitokoto']} - {hitokoto_json['from']}（{hitokoto_type[hitokoto_json['type']]}）")
