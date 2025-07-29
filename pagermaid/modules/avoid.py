"""PagerMaid module for different ways to avoid users."""

from pagermaid.dependence import sqlite
from pagermaid.enums import Client, Message
from pagermaid.enums.command import CommandHandler
from pagermaid.listener import listener
from pagermaid.utils import lang
from pagermaid.utils.bot_utils import log


@listener(
    is_plugin=False,
    command="ghost",
    description=lang("ghost_des"),
    parameters="<true|false|status>",
)
async def ghost(message: Message):
    """Toggles ghosting of a user."""
    await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")


ghost: "CommandHandler"


@ghost.sub_command(
    is_plugin=False,
    command="true",
)
async def ghost_true(client: Client, message: Message):
    myself = await client.get_me()
    self_user_id = myself.id
    if message.chat_id == self_user_id:
        return await message.edit(lang("ghost_e_mark"))
    sqlite[f"ghosted.chat_id.{str(message.chat_id)}"] = True
    await message.safe_delete()
    await log(
        f"{lang('ghost_set_f')} ChatID {str(message.chat_id)} {lang('ghost_set_l')}"
    )


@ghost.sub_command(
    is_plugin=False,
    command="false",
)
async def ghost_false(client: Client, message: Message):
    myself = await client.get_me()
    self_user_id = myself.id
    if message.chat_id == self_user_id:
        await message.edit(lang("ghost_e_mark"))
        return
    try:
        del sqlite[f"ghosted.chat_id.{str(message.chat_id)}"]
    except KeyError:
        return await message.edit(lang("ghost_e_noexist"))
    await message.safe_delete()
    await log(
        f"{lang('ghost_set_f')} ChatID {str(message.chat_id)} {lang('ghost_cancel')}"
    )


@ghost.sub_command(
    is_plugin=False,
    command="status",
)
async def ghost_status(message: Message):
    if sqlite.get(f"ghosted.chat_id.{str(message.chat_id)}", None):
        await message.edit(lang("ghost_e_exist"))
    else:
        await message.edit(lang("ghost_e_noexist"))


@listener(
    is_plugin=False,
    command="deny",
    need_admin=True,
    description=lang("deny_des"),
    parameters="<true|false|status>",
)
async def deny(message: Message):
    """Toggles denying of a user."""
    await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")


deny: "CommandHandler"


@deny.sub_command(
    is_plugin=False,
    need_admin=True,
    command="true",
)
async def deny_true(client: Client, message: Message):
    myself = await client.get_me()
    self_user_id = myself.id
    if message.chat_id == self_user_id:
        return await message.edit(lang("ghost_e_mark"))
    sqlite[f"denied.chat_id.{str(message.chat_id)}"] = True
    await message.safe_delete()
    await log(f"ChatID {str(message.chat_id)} {lang('deny_set')}")


@deny.sub_command(
    is_plugin=False,
    need_admin=True,
    command="false",
)
async def deny_false(client: Client, message: Message):
    myself = await client.get_me()
    self_user_id = myself.id
    if message.chat_id == self_user_id:
        await message.edit(lang("ghost_e_mark"))
        return
    try:
        del sqlite[f"denied.chat_id.{str(message.chat_id)}"]
    except KeyError:
        return await message.edit(lang("deny_e_noexist"))
    await message.safe_delete()
    await log(f"ChatID {str(message.chat_id)} {lang('deny_cancel')}")


@deny.sub_command(
    is_plugin=False,
    need_admin=True,
    command="status",
)
async def deny_status(message: Message):
    if sqlite.get(f"denied.chat_id.{str(message.chat_id)}", None):
        await message.edit(lang("deny_e_exist"))
    else:
        await message.edit(lang("deny_e_noexist"))


@listener(is_plugin=False, incoming=True, ignore_edited=True)
async def set_read_acknowledgement(context: Message):
    """Event handler to infinitely read ghosted messages."""
    if sqlite.get(f"ghosted.chat_id.{str(context.chat_id)}", None):
        try:
            await context.client.send_read_acknowledge(context.chat_id)
        except ValueError:
            pass


@listener(is_plugin=False, incoming=True, ignore_edited=True)
async def message_removal(context: Message):
    """Event handler to infinitely delete denied messages."""
    if sqlite.get(f"denied.chat_id.{str(context.chat_id)}", None):
        await context.safe_delete()
