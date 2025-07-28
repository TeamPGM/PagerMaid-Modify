"""Module to automate message deletion."""

import contextlib
from asyncio import sleep

from pagermaid.enums import Message
from pagermaid.listener import listener
from pagermaid.utils import lang
from pagermaid.utils.bot_utils import log


@listener(
    is_plugin=False,
    outgoing=True,
    command="prune",
    need_admin=True,
    description=lang("prune_des"),
)
async def prune(context: Message):
    """Purge every single message after the message you replied to."""
    if not context.reply_to_msg_id:
        await context.edit(lang("not_reply"))
        return
    input_chat = await context.get_input_chat()
    messages = []
    count = 0
    limit = context.id - context.reply_to_msg_id + 1
    async for message in context.client.iter_messages(
        input_chat, min_id=context.reply_to_msg_id, limit=limit
    ):
        messages.append(message)
        count += 1
        messages.append(context.reply_to_msg_id)
        if len(messages) == 100:
            await context.client.delete_messages(input_chat, messages)
            messages = []

    if messages:
        await context.client.delete_messages(input_chat, messages)
    await log(f"{lang('prune_hint1')} {str(count)} {lang('prune_hint2')}")
    notification = await send_prune_notify(context, count, count)
    await sleep(1)
    await notification.delete()


@listener(
    is_plugin=False,
    outgoing=True,
    command="selfprune",
    need_admin=True,
    description=lang("sp_des"),
    parameters=lang("sp_parameters"),
)
async def self_prune(message: Message):
    """Deletes specific amount of messages you sent."""
    msgs = []
    count_buffer = 0
    offset = 0
    if len(message.parameter) != 1:
        if not message.reply_to_msg_id:
            return await message.edit(lang("arg_error"))
        offset = message.reply_to_msg_id
    if message.parameter:
        try:
            count = int(message.parameter[0])
            await message.delete()
        except ValueError:
            await message.edit(lang("arg_error"))
            return None
    else:
        count = message.id - offset
    async for message in message.client.iter_messages(
        message.chat_id, from_user="me", min_id=offset
    ):
        if count_buffer == count:
            break
        msgs.append(message)
        count_buffer += 1
        if len(msgs) == 100:
            await message.client.delete_messages(message.chat_id, msgs)
            msgs = []
    if msgs:
        await message.client.delete_messages(message.chat_id, msgs)
    await log(
        f"{lang('prune_hint1')}{lang('sp_hint')} {str(count_buffer)} / {count} {lang('prune_hint2')}"
    )

    with contextlib.suppress(ValueError):
        notification = await send_prune_notify(message, count_buffer, count)
        await sleep(1)
        await notification.delete()
    return None


@listener(
    is_plugin=False,
    outgoing=True,
    command="yourprune",
    need_admin=True,
    description=lang("yp_des"),
    parameters=lang("sp_parameters"),
)
async def your_prune(message: Message):
    """Deletes specific amount of messages someone sent."""
    if not message.reply_to_msg_id:
        return await message.edit(lang("not_reply"))
    target = await message.get_reply_message()
    if not target:
        return await message.edit(lang("not_reply"))
    if len(message.parameter) != 1:
        return await message.edit(lang("arg_error"))
    count = 0
    try:
        count = int(message.parameter[0])
        await message.delete()
    except ValueError:
        return await message.edit(lang("arg_error"))
    except Exception:  # noqa
        pass
    count_buffer = 0
    msgs = []
    async for message in message.client.iter_messages(
        message.chat_id,
        from_user=target.sender_id,
    ):
        if count_buffer == count:
            break
        count_buffer += 1
        msgs.append(message)
        if len(msgs) == 100:
            await message.client.delete_messages(message.chat_id, msgs)
            msgs = []
    if msgs:
        await message.client.delete_messages(message.chat_id, msgs)
    await log(
        f"{lang('prune_hint1')}{lang('yp_hint')} {str(count_buffer)} / {count} {lang('prune_hint2')}"
    )

    with contextlib.suppress(ValueError):
        notification = await send_prune_notify(message, count_buffer, count)
        await sleep(1)
        await notification.delete()
    return None


@listener(
    is_plugin=False,
    outgoing=True,
    command="del",
    need_admin=True,
    description=lang("del_des"),
)
async def delete(message: Message):
    """Deletes the message you replied to."""
    target = await message.get_reply_message()
    if message.reply_to_msg_id:
        with contextlib.suppress(Exception):
            await target.delete()
        await message.safe_delete()
        await log(lang("del_notification"))
    else:
        await message.safe_delete()


async def send_prune_notify(context: "Message", count_buffer, count):
    return await context.client.send_message(
        context.chat_id,
        "%s %s / %s %s"
        % (lang("spn_deleted"), str(count_buffer), str(count), lang("prune_hint2")),
    )
