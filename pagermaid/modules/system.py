"""System related utilities for PagerMaid to integrate into the system."""

import html
import sys
from getpass import getuser
from os.path import exists, sep
from platform import node
from time import perf_counter
from typing import TYPE_CHECKING

from pagermaid.common.system import run_eval, paste_pb, process_exit
from pagermaid.config import Config
from pagermaid.hook import Hook
from pagermaid.listener import listener
from pagermaid.utils import execute, lang
from pagermaid.utils.bot_utils import attach_log, upload_attachment

if TYPE_CHECKING:
    from pagermaid.enums import Client, Message

code_result = (
    f"<b>{lang('eval_code')}</b>\n"
    '<pre language="{}">{}</pre>\n\n'
    f"<b>{lang('eval_result')}</b>\n"
    "{}\n"
    f"<b>{lang('eval_time')}</b>"
)


@listener(
    is_plugin=False,
    command="sh",
    need_admin=True,
    description=lang("sh_des"),
    parameters=lang("sh_parameters"),
)
async def sh(message: "Message"):
    """Use the command-line from Telegram."""
    user = getuser()
    command = message.arguments
    hostname = node()

    if not command:
        await message.edit(lang("arg_error"))
        return

    message = await message.edit(
        f"`{user}`@{hostname} ~\n> `$` {command}", parse_mode="md"
    )

    result = await execute(command)

    if result:
        final_result = None
        if len(result) > 3072:
            if Config.USE_PB:
                url = await paste_pb(result)
                if url:
                    final_result = f"{url}/bash"
        else:
            final_result = result

        if (len(result) > 3072 and not Config.USE_PB) or final_result is None:
            await attach_log(result, message.chat_id, "output.log", message.id)
            return
        await message.edit(
            f"`{user}`@{hostname} ~\n> `#` {command}\n\n`{final_result}`",
            parse_mode="md",
        )
    else:
        return


@listener(
    is_plugin=False, command="restart", need_admin=True, description=lang("restart_des")
)
async def restart(message: "Message"):
    """To re-execute PagerMaid."""
    if not message.text[0].isalpha():
        await message.edit(lang("restart_log"))
        sys.exit(0)


@Hook.on_shutdown()
async def restart_shutdown_hook(client: "Client", message: "Message"):
    await process_exit(start=False, _client=client, message=message)


@Hook.on_startup()
async def restart_startup_hook(client: "Client"):
    await process_exit(start=True, _client=client)


@listener(
    is_plugin=False,
    command="eval",
    need_admin=True,
    description=lang("eval_des"),
    parameters=lang("eval_parameters"),
)
async def sh_eval(message: "Message"):
    """Run python commands from Telegram."""
    dev_mode = exists(f"data{sep}dev")
    try:
        if not dev_mode:
            raise AssertionError
        cmd = message.text.split(" ", maxsplit=1)[1]
    except (IndexError, AssertionError):
        return await message.edit(lang("eval_need_dev"))
    message = await message.edit(f"<b>{lang('eval_executing')}</b>", parse_mode="html")
    start_time = perf_counter()
    final_output = await run_eval(cmd, message)
    stop_time = perf_counter()

    result = None
    if len(final_output) > 3072:
        if Config.USE_PB:
            url = await paste_pb(final_output)
            if url:
                result = html.escape(f"{url}/python")
    else:
        result = f"<code>{html.escape(final_output)}</code>"
    text = code_result.format(
        "python",
        html.escape(cmd),
        result if result else "...",
        round(stop_time - start_time, 5),
    )

    await message.edit(text, parse_mode="html")
    if (len(final_output) > 3072 and not Config.USE_PB) or result is None:
        await attach_log(final_output, message.chat_id, "output.log", message.id)
    return None


@listener(
    is_plugin=False,
    command="send_log",
    need_admin=True,
    description=lang("send_log_des"),
)
async def send_log(message: "Message"):
    """Send log to a chat."""
    if not exists("data/pagermaid.log.txt"):
        return await message.edit(lang("send_log_not_found"))
    await upload_attachment(
        "data/pagermaid.log.txt",
        message.chat_id,
        message.reply_to_msg_id,
        thumb=f"pagermaid{sep}assets{sep}logo.jpg",
        caption=lang("send_log_caption"),
    )
    await message.safe_delete()
    return None
