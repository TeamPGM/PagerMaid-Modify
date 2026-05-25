"""PagerMaid event listener."""

import asyncio
import contextlib
import sys
from asyncio import CancelledError
from time import strftime, gmtime, time
from traceback import format_exc

from telethon import events
from telethon.errors import (
    MessageTooLongError,
    MessageNotModifiedError,
    MessageEmptyError,
    UserNotParticipantError,
    ForbiddenError,
    PeerIdInvalidError,
    MessageIdInvalidError,
)
from telethon.events import StopPropagation

from pagermaid.common.ignore import ignore_groups_manager
from pagermaid.config import Config
from pagermaid.enums import Message
from pagermaid.enums.command import CommandHandler, CommandHandlerDecorator
from pagermaid.group_manager import Permission
from pagermaid.hook import HookRunner
from pagermaid.services import bot
from pagermaid.static import help_messages, read_context, all_permissions
from pagermaid.utils import (
    lang,
    alias_command,
    logs,
)
from pagermaid.utils.bot_utils import attach_report
from pagermaid.utils.listener import (
    get_permission_name,
    format_exc as format_exc_text,
    sudo_filter,
)
from pagermaid.web import web
from pyromod.utils.handler_priority import HandlerList

_lock = asyncio.Lock()


def listener(**args) -> CommandHandlerDecorator:
    """Register an event listener."""
    parent_command = args.get("__parent_command")
    command = args.get("command")
    allow_parent = args.get("allow_parent", False)
    disallow_alias = args.get("disallow_alias", False)
    need_admin = args.get("need_admin", False)
    description = args.get("description", None)
    parameters = args.get("parameters", None)
    pattern = sudo_pattern = args.get("pattern")
    diagnostics = args.get("diagnostics", True)
    incoming = args.get("incoming", False)
    outgoing = args.get("outgoing", True)
    args["incoming"] = incoming
    args["outgoing"] = outgoing
    ignore_edited = args.get("ignore_edited", False)
    ignore_reacted = args.get("ignore_reacted", True)
    ignore_forwarded = args.get("ignore_forwarded", True if outgoing else False)
    is_plugin = args.get("is_plugin", True)
    groups_only = args.get("groups_only", False)
    privates_only = args.get("privates_only", False)
    support_inline = args.get("support_inline", False)
    priority = args.get("priority", 50)
    block_process = args.get("block_process", False)

    if priority < 0 or priority > 100:
        raise ValueError("Priority must be between 0 and 100.")
    elif priority == 0 and is_plugin:
        """Priority 0 is reserved for modules."""
        priority = 1
    elif (not is_plugin) and need_admin:
        priority = 0

    if command is not None:
        if parent_command is None and command in help_messages:
            if help_messages[alias_command(command)]["priority"] <= priority:
                raise ValueError(
                    f'{lang("error_prefix")} {lang("command")} "{command}" {lang("has_reg")}'
                )
            else:
                block_process = True
        real_command = (
            alias_command(command, disallow_alias)
            if parent_command is None
            else f"{parent_command} {command}"
        )
        pattern = rf"^(-){real_command}(?: |$)([\s\S]*)"
        sudo_pattern = rf"^(/){real_command}(?: |$)([\s\S]*)"
    if pattern is not None and not pattern.startswith("(?i)"):
        args["pattern"] = f"(?i){pattern}"
    else:
        args["pattern"] = pattern
    if sudo_pattern is not None and not sudo_pattern.startswith("(?i)"):
        sudo_pattern = f"(?i){sudo_pattern}"
    permission_name = get_permission_name(is_plugin, need_admin, command)

    for key in (
        "__parent_command",
        "command",
        "allow_parent",
        "disallow_alias",
        "need_admin",
        "description",
        "parameters",
        "diagnostics",
        "ignore_edited",
        "ignore_reacted",
        "ignore_forwarded",
        "is_plugin",
        "groups_only",
        "privates_only",
        "support_inline",
        "priority",
        "block_process",
    ):
        if key in args:
            del args[key]

    def decorator(function) -> CommandHandler:
        func = CommandHandler(
            function,
            (
                alias_command(command, disallow_alias)
                if command and parent_command is None
                else None
            ),
        )

        async def handler(context: "Message"):
            if groups_only and not context.is_group:
                return
            if privates_only and not context.is_private:
                return
            if not support_inline and context.via_bot_id:
                return
            if ignore_forwarded and context.forward is not None:
                return
            try:
                # ignore
                try:
                    if ignore_groups_manager.check_id(context.chat_id):
                        return
                except BaseException:
                    pass
                try:
                    arguments = context.pattern_match.group(2)
                    parameter = arguments.split(" ")
                    if parameter == [""]:
                        parameter = []
                    if parent_command is not None and command is not None:
                        parameter.insert(0, command)
                        arguments = f"{command} {arguments}".strip()
                    if (
                        getattr(handler, CommandHandler.ignore_sub_commands_key, False)
                        and len(arguments) > 0
                    ):
                        return
                    context.parameter = parameter
                    context.arguments = arguments
                except BaseException:
                    context.parameter = None
                    context.arguments = None
                # solve same process
                async with _lock:
                    if (context.chat_id, context.id) in read_context:
                        return
                    read_context[(context.chat_id, context.id)] = True

                if command:
                    await HookRunner.command_pre(
                        context,
                        parent_command or command,
                        command if parent_command else None,
                    )
                await func.handler(context)
                if command:
                    await HookRunner.command_post(
                        context,
                        parent_command or command,
                        command if parent_command else None,
                    )
            except StopPropagation:
                raise StopPropagation
            except KeyboardInterrupt as e:
                raise KeyboardInterrupt from e
            except MessageTooLongError:
                await context.edit(lang("too_long"))
            except (
                UserNotParticipantError,
                MessageNotModifiedError,
                MessageEmptyError,
                ForbiddenError,
                PeerIdInvalidError,
            ):
                logs.warning(
                    "An unknown chat error occurred while processing a command.",
                )
            except MessageIdInvalidError:
                logs.warning("Please Don't Delete Commands While it's Processing..")
            except (SystemExit, CancelledError):
                await HookRunner.shutdown(context)
                web.stop()
            except BaseException as exc:
                exc_info = sys.exc_info()[1]
                exc_format = format_exc()
                with contextlib.suppress(BaseException):
                    exc_text = format_exc_text(exc)
                    text = f"{lang('run_error')}\n\n{exc_text}"
                    await context.edit(text, no_reply=True)  # noqa
                if not diagnostics:
                    return
                report = (
                    f"# Generated: {strftime('%H:%M %d/%m/%Y', gmtime())}. \n"
                    f"# ChatID: {str(context.chat_id)}. \n"
                    f"# UserID: {str(context.sender_id)}. \n"
                    f"# Message: \n-----BEGIN TARGET MESSAGE-----\n"
                    f"{context.text}\n-----END TARGET MESSAGE-----\n"
                    f"# Traceback: \n-----BEGIN TRACEBACK-----\n"
                    f"{str(exc_format)}\n-----END TRACEBACK-----\n"
                    f'# Error: "{str(exc_info)}". \n'
                )

                logs.error(report)
                if Config.ERROR_REPORT:
                    await attach_report(
                        report,
                        f"exception.{time()}.pgm.txt",
                        None,
                        "PGM Error report generated.",
                    )
                await HookRunner.process_error_exec(
                    context, command, exc_info, exc_format
                )
            finally:
                if (context.chat_id, context.id) in read_context:
                    del read_context[(context.chat_id, context.id)]
            if block_process or (parent_command and not allow_parent):
                raise StopPropagation

        setattr(handler, HandlerList.PRIORITY_KEY, priority)
        bot.add_event_handler(handler, events.NewMessage(**args))
        if not ignore_edited:
            bot.add_event_handler(handler, events.MessageEdited(**args))
        if command and pattern and sudo_pattern:
            sudo_args = args.copy()
            sudo_args["pattern"] = sudo_pattern
            sudo_args["incoming"] = True
            sudo_args["outgoing"] = False
            sudo_handler = sudo_filter(permission_name, handler)
            setattr(sudo_handler, HandlerList.PRIORITY_KEY, 50 + priority)
            bot.add_event_handler(sudo_handler, events.NewMessage(**sudo_args))
            if not ignore_edited:
                bot.add_event_handler(sudo_handler, events.MessageEdited(**sudo_args))

        func.set_handler(handler)
        return func

    if description is not None and command is not None and parent_command is None:
        if parameters is None:
            parameters = ""
        help_messages.update(
            {
                f"{alias_command(command)}": {
                    "permission": permission_name,
                    "use": f"**{lang('use_method')}:** `-{command} {parameters}`\n"
                    f"**{lang('need_permission')}:** `{permission_name}`\n"
                    f"{description}",
                    "priority": priority,
                }
            }
        )
        all_permissions.append(Permission(permission_name))

    return decorator
