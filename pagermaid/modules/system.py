""" System related utilities for PagerMaid to integrate into the system. """

import io, sys, traceback
from os.path import exists
from platform import node
from getpass import getuser
from os import geteuid, sep
from requests import head
from asyncio import sleep
from requests.exceptions import MissingSchema, InvalidURL, ConnectionError
from pagermaid import log, bot, redis_status, redis, silent
from pagermaid.listener import listener
from pagermaid.utils import attach_log, execute, lang, alias_command
from telethon.errors.rpcerrorlist import UserAlreadyParticipantError
from telethon.tl.functions.messages import ImportChatInviteRequest


@listener(is_plugin=False, outgoing=True, command=alias_command("sh"),
          description=lang('sh_des'),
          parameters=lang('sh_parameters'))
async def sh(context):
    """ Use the command-line from Telegram. """
    user = getuser()
    command = context.arguments
    hostname = node()
    if context.is_channel and not context.is_group:
        await context.edit(lang('sh_channel'))
        return

    if not command:
        await context.edit(lang('arg_error'))
        return

    if geteuid() == 0:
        await context.edit(
            f"`{user}`@{hostname} ~"
            f"\n> `#` {command}"
        )
    else:
        await context.edit(
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
            await context.edit(
                f"`{user}`@{hostname} ~"
                f"\n> `#` {command}"
                f"\n`{result}`"
            )
        else:
            await context.edit(
                f"`{user}`@{hostname} ~"
                f"\n> `$` {command}"
                f"\n`{result}`"
            )
    else:
        return
    await log(f"{lang('sh_success')}: `{command}`")


@listener(is_plugin=False, outgoing=True, command="eval",
          description=lang('eval_des'),
          parameters=lang('eval_parameters'))
async def sh(context):
    """ Run python commands from Telegram. """
    dev_mode = False
    # file
    if exists(f"data{sep}dev"):
        dev_mode = True
    # redis
    if redis_status():
        if redis.get("dev"):
            dev_mode = True
    if not dev_mode:
        return await context.edit(lang('eval_need_dev'))
    if context.is_channel and not context.is_group:
        await context.edit(lang('eval_channel'))
        return
    try:
        cmd = context.text.split(" ", maxsplit=1)[1]
    except IndexError:
        await context.edit(lang('arg_error'))
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
        await context.edit("**>>>** ```{}```".format(cmd))
        await attach_log(evaluation, context.chat_id, "output.log", context.id)
    else:
        await context.edit(final_output)
    await log(f"{lang('eval_success')}: `{cmd}`")


@listener(is_plugin=False, outgoing=True, command=alias_command("restart"), diagnostics=False,
          description=lang('restart_des'))
async def restart(context):
    """ To re-execute PagerMaid. """
    if not context.text[0].isalpha():
        try:
            result = await context.edit(lang('restart_processing'))
            if redis_status():
                redis.set("restart_edit", f"{result.id}|{result.chat_id}")

        except:  # noqa
            pass
        await log(lang('restart_log'))
        await context.client.disconnect()


@listener(is_plugin=False, outgoing=True, command=alias_command("trace"),
          description=lang('trace_des'),
          parameters="<url>")
async def trace(context):
    """ Trace URL redirects. """
    url = context.arguments
    reply = await context.get_reply_message()
    if reply:
        url = reply.text
    if url:
        if url.startswith("https://") or url.startswith("http://"):
            pass
        else:
            url = "https://" + url
        if not silent:
            await context.edit(lang('trace_processing'))
        result = str("")
        for url in url_tracer(url):
            count = 0
            if result:
                result += " ↴\n" + url
            else:
                result = url
            if count == 128:
                result += f"\n\n{lang('trace_over128')}"
                break
        if result:
            if len(result) > 4096:
                await context.edit(lang('translate_tg_limit_uploading_file'))
                await attach_log(result, context.chat_id, "output.log", context.id)
                return
            await context.edit(
                f"{lang('trace_re')}:\n"
                f"{result}"
            )
            await log(f"Traced redirects of {context.arguments}.")
        else:
            await context.edit(lang('trace_http_error'))
    else:
        await context.edit(lang('arg_error'))


@listener(is_plugin=False, outgoing=True, command=alias_command("chat"),
          description=lang('chat_des'))
async def contact_chat(context):
    """ join a chatroom. """
    results = await context.client.inline_query('Invite_Challenge_Bot', '1')
    await results[0].click(context.chat_id)
    await context.delete()


def url_tracer(url):
    """ Method to trace URL redirects. """
    while True:
        yield url
        try:
            response = head(url)
        except MissingSchema:
            break
        except InvalidURL:
            break
        except ConnectionError:
            break
        if 300 < response.status_code < 400:
            url = response.headers['location']
        else:
            break


async def aexec(code, event):
    exec(
        f"async def __aexec(e, client): "
        + "\n msg = context = e"
        + "\n reply = await context.get_reply_message()"
        + "\n chat = e.chat_id"
        + "".join(f"\n {l}" for l in code.split("\n")),
    )

    return await locals()["__aexec"](event, event.client)
