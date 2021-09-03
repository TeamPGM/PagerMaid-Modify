from pagermaid import log, redis, redis_status
from pagermaid.listener import listener
from pagermaid.utils import lang, alias_command
from struct import error as StructError
from telethon.tl.functions.messages import GetCommonChatsRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageEntityMentionName, ChannelParticipantsAdmins
from telethon.errors.rpcerrorlist import UserAdminInvalidError, ChatAdminRequiredError, FloodWaitError
from asyncio import sleep
from random import uniform


def mention_user(user):
    try:
        first_name = user.first_name.replace("\u2060", "")
    except AttributeError:
        first_name = '×'
    return f'[{first_name}](tg://user?id={user.id})'


def mention_group(chat):
    try:
        if chat.username:
            if chat.username:
                text = f'[{chat.title}](https://t.me/{chat.username})'
            else:
                text = f'`{chat.title}`'
        else:
            text = f'`{chat.title}`'
    except AttributeError:
        text = f'`{chat.title}`'
    return text


@listener(is_plugin=False, outgoing=True, command=alias_command("sb"),
          description=lang('sb_des'),
          parameters="<reply|id|username>")
async def span_ban(context):
    if context.reply_to_msg_id:
        reply_message = await context.get_reply_message()
        if reply_message:
            try:
                user = reply_message.from_id
            except AttributeError:
                await context.edit(lang('arg_error'))
                return
        else:
            await context.edit(lang('arg_error'))
            return
        target_user = await context.client(GetFullUserRequest(user))
    else:
        if len(context.parameter) == 1:
            user = context.parameter[0]
            if user.isnumeric():
                user = int(user)
        else:
            await context.edit(lang('arg_error'))
            return
        if context.message.entities is not None:
            if isinstance(context.message.entities[0], MessageEntityMentionName):
                user = context.message.entities[0].user_id
            else:
                await context.edit(f"{lang('error_prefix')}{lang('arg_error')}")
                return
        try:
            user_object = await context.client.get_entity(user)
            target_user = await context.client(GetFullUserRequest(user_object.id))
        except (TypeError, ValueError, OverflowError, StructError) as exception:
            if str(exception).startswith("Cannot find any entity corresponding to"):
                await context.edit(f"{lang('error_prefix')}{lang('profile_e_no')}")
                return
            if str(exception).startswith("No user has"):
                await context.edit(f"{lang('error_prefix')}{lang('profile_e_nou')}")
                return
            if str(exception).startswith("Could not find the input entity for") or isinstance(exception, StructError):
                await context.edit(f"{lang('error_prefix')}{lang('profile_e_nof')}")
                return
            if isinstance(exception, OverflowError):
                await context.edit(f"{lang('error_prefix')}{lang('profile_e_long')}")
                return
            raise exception
    myself = await context.client.get_me()
    self_user_id = myself.id
    if target_user.user.id == self_user_id:
        await context.edit(lang('arg_error'))
        return
    result = await context.client(GetCommonChatsRequest(user_id=target_user, max_id=0, limit=100))
    count = 0
    groups = []
    for i in result.chats:
        try:
            await context.client.edit_permissions(i.id, target_user, view_messages=False)
            groups.append(mention_group(i))
            count += 1
        except FloodWaitError as e:
            # Wait flood secs
            await context.edit(f'{lang("sb_pause")} {e.seconds + uniform(0.5, 1.0)} s.')
            try:
                await sleep(e.seconds + uniform(0.5, 1.0))
            except Exception as e:
                print(f"Wait flood error: {e}")
                return
        except UserAdminInvalidError:
            pass
        except ChatAdminRequiredError:
            pass
        except ValueError:
            pass
    if redis_status():
        sb_groups = redis.get('sb_groups')
        if sb_groups:
            sb_groups = sb_groups.decode()
            sb_groups = sb_groups.split('|')
            try:
                sb_groups.remove('')
            except ValueError:
                pass
        else:
            sb_groups = []
        for i in sb_groups:
            try:
                chat = await context.client.get_entity(int(i))
                await context.client.edit_permissions(chat, target_user, view_messages=False)
                groups.append(mention_group(chat))
                count += 1
            except FloodWaitError as e:
                # Wait flood secs
                await context.edit(f'{lang("sb_pause")} {e.seconds + uniform(0.5, 1.0)} s.')
                try:
                    await sleep(e.seconds + uniform(0.5, 1.0))
                except Exception as e:
                    print(f"Wait flood error: {e}")
                    return
            except UserAdminInvalidError:
                pass
            except ChatAdminRequiredError:
                pass
    if count == 0:
        text = f'{lang("sb_no")} {mention_user(target_user.user)}'
    else:
        text = f'{lang("sb_per")} {count} {lang("sb_in")} {mention_user(target_user.user)}'
    await context.edit(text)
    if len(groups) > 0:
        groups = f'\n{lang("sb_pro")}\n' + "\n".join(groups)
    else:
        groups = ''
    await log(f'{text}\nuid: `{target_user.user.id}` {groups}')


@listener(is_plugin=False, outgoing=True, command=alias_command("sb_set"),
          description=lang('sb_des_auto'),
          parameters="<true|false|status>")
async def span_ban_Set(context):
    """ Toggles sb of a group. """
    if not redis_status():
        await context.edit(f"{lang('error_prefix')}{lang('redis_dis')}")
        return
    if len(context.parameter) != 1:
        await context.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        return
    if not context.is_group:
        await context.edit(lang('ghost_e_mark'))
        return
    admins = await context.client.get_participants(context.chat, filter=ChannelParticipantsAdmins)
    if context.sender in admins:
        user = admins[admins.index(context.sender)]
        if not user.participant.admin_rights.ban_users:
            await context.edit(lang('sb_no_per'))
            return
    else:
        await context.edit(lang('sb_no_per'))
        return
    groups = redis.get('sb_groups')
    if groups:
        groups = groups.decode()
        groups = groups.split('|')
        try:
            groups.remove('')
        except ValueError:
            pass
    else:
        groups = []
    if context.parameter[0] == "true":
        if str(context.chat_id) not in groups:
            groups.append(str(context.chat_id))
            groups = '|'.join(groups)
            redis.set('sb_groups', groups)
            await context.edit(f"ChatID {str(context.chat_id)} {lang('sb_set')}")
            await log(f"ChatID {str(context.chat_id)} {lang('sb_set')}")
        else:
            await context.edit(f"ChatID {str(context.chat_id)} {lang('sb_set')}")
    elif context.parameter[0] == "false":
        if str(context.chat_id) in groups:
            groups.remove(str(context.chat_id))
            groups = '|'.join(groups)
            redis.set('sb_groups', groups)
            await context.edit(f"ChatID {str(context.chat_id)} {lang('sb_remove')}")
            await log(f"ChatID {str(context.chat_id)} {lang('sb_remove')}")
        else:
            await context.edit(f"ChatID {str(context.chat_id)} {lang('sb_remove')}")
    elif context.parameter[0] == "status":
        if str(context.chat_id) in groups:
            await context.edit(lang('sb_exist'))
        else:
            await context.edit(lang('sb_no_exist'))
    else:
        await context.edit(f"{lang('error_prefix')}{lang('arg_error')}")
