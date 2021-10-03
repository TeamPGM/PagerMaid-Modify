""" System related utilities for PagerMaid to integrate into the system. """

import io, sys, traceback
from platform import node
from getpass import getuser
from os import geteuid
from pagermaid import log, redis_status, redis
from pagermaid.listener import listener
from pagermaid.utils import attach_log, execute, lang, alias_command


@listener(is_plugin=False, incoming=True, owners_only=True, command=alias_command("sh"),
          description=lang('sh_des'),
          parameters=lang('sh_parameters'))
async def sh(context):
    """ Use the command-line from Telegram. """
    user = getuser()
    command = context.arguments
    hostname = node()
    if context.is_channel and not context.is_group:
        await context.reply(lang('sh_channel'))
        return

    if not command:
        await context.reply(lang('arg_error'))
        return

    if geteuid() == 0:
        msg = await context.reply(
            f"`{user}`@{hostname} ~"
            f"\n> `#` {command}"
        )
    else:
        msg = await context.reply(
            f"`{user}`@{hostname} ~"
            f"\n> `$` {command}"
        )

    try:
        result = await execute(command)
    except UnicodeDecodeError as e:
        result = str(e)

    if result:
        if len(result) > 4096:
            await attach_log(result, context.chat_id, "output.log", context.id)
            return

        if geteuid() == 0:
            await msg.edit(
                f"`{user}`@{hostname} ~"
                f"\n> `#` {command}"
                f"\n`{result}`"
            )
        else:
            await msg.edit(
                f"`{user}`@{hostname} ~"
                f"\n> `$` {command}"
                f"\n`{result}`"
            )
    else:
        return
    await log(f"{lang('sh_success')}: `{command}`")


@listener(is_plugin=False, incoming=True, owners_only=True, command="eval",
          description=lang('eval_des'),
          parameters=lang('eval_parameters'))
async def sh(context):
    """ Run python commands from Telegram. """
    if not redis_status():
        await context.reply(f"{lang('error_prefix')}{lang('redis_dis')}")
        return
    if not redis.get("dev"):
        await context.reply(lang('eval_need_dev'))
        return
    if context.is_channel and not context.is_group:
        await context.reply(lang('eval_channel'))
        return
    try:
        cmd = context.text.split(" ", maxsplit=1)[1]
    except IndexError:
        await context.reply(lang('arg_error'))
        return
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None
    try:
        await aexec(cmd, context)
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"
    final_output = (
        "**>>>** ```{}``` \n```{}```".format(
            cmd,
            evaluation,
        )
    )
    if len(final_output) > 4096:
        await context.reply("**>>>** ```{}```".format(cmd))
        await attach_log(evaluation, context.chat_id, "output.log", context.id)
    else:
        await context.reply(final_output)
    await log(f"{lang('eval_success')}: `{cmd}`")


@listener(is_plugin=False, incoming=True, owners_only=True, command=alias_command("restart"), diagnostics=False,
          description=lang('restart_des'))
async def restart(context):
    """ To re-execute PagerMaid. """
    if not context.text[0].isalpha():
        await context.reply(lang('restart_processing'))
        await log(lang('restart_log'))
        await context.client.disconnect()


async def aexec(code, event):
    exec(
        f"async def __aexec(e, client): "
        + "\n msg = context = e"
        + "\n reply = await context.get_reply_message()"
        + "\n chat = e.chat_id"
        + "".join(f"\n {l}" for l in code.split("\n")),
    )

    return await locals()["__aexec"](event, event.client)
