""" PagerMaid event listener. """

import re
import sentry_sdk
import sys
from distutils.util import strtobool
from time import gmtime, strftime, time
from traceback import format_exc

from telethon import events
from telethon.errors import MessageTooLongError
from telethon.events import StopPropagation
from telethon.tl.types import PeerUser

from pagermaid import bot, config, help_messages, logs, user_id, analytics, user_bot
from pagermaid.utils import attach_report, lang, alias_command, admin_check

try:
    allow_analytics = strtobool(config['allow_analytic'])
except KeyError:
    allow_analytics = True
except ValueError:
    allow_analytics = True


def noop(*args, **kw):
    pass


def listener(**args):
    """ Register an event listener. """
    command = args.get('command', None)
    description = args.get('description', None)
    parameters = args.get('parameters', None)
    pattern = args.get('pattern', None)
    diagnostics = args.get('diagnostics', True)
    ignore_edited = args.get('ignore_edited', False)
    is_plugin = args.get('is_plugin', True)
    owners_only = args.get("owners_only", False)
    admins_only = args.get("admins_only", False)
    groups_only = args.get("groups_only", False)
    support_inline = args.get("support_inline", False)
    if command is not None:
        if command in help_messages:
            raise ValueError(f"{lang('error_prefix')} {lang('command')} \"{command}\" {lang('has_reg')}")
        pattern = fr"^-{command}(?: |$)([\s\S]*)"
        if user_bot:
            pattern = fr"^/{command}(@{user_bot})?(?: |$)([\s\S]*)"
    if pattern is not None and not pattern.startswith('(?i)'):
        args['pattern'] = f"(?i){pattern}"
    else:
        args['pattern'] = pattern
    if 'ignore_edited' in args:
        del args['ignore_edited']
    if 'command' in args:
        del args['command']
    if 'diagnostics' in args:
        del args['diagnostics']
    if 'description' in args:
        del args['description']
    if 'parameters' in args:
        del args['parameters']
    if 'is_plugin' in args:
        del args['is_plugin']
    if 'owners_only' in args:
        del args['owners_only']
    if 'admins_only' in args:
        del args['admins_only']
    if 'groups_only' in args:
        del args['groups_only']
    if 'support_inline' in args:
        del args['support_inline']

    def decorator(function):

        async def handler(context):
            # bot admin command
            if owners_only:
                if context.sender_id and 'bot_admins' in config:
                    if config['bot_admins'].count(context.sender_id) == 0:
                        return
                else:
                    return
            # group admin command
            if admins_only:
                if not (await admin_check(context)):
                    return
            # groups only
            if groups_only:
                if not context.is_group:
                    return
            # filter inline bot msg
            if not support_inline and context.via_bot_id:
                return
            try:
                analytic = True
                try:
                    if user_bot:
                        parameter = context.pattern_match.group(2).split(' ')
                    else:
                        parameter = context.pattern_match.group(1).split(' ')
                    if parameter == ['']:
                        parameter = []
                    context.parameter = parameter
                    if user_bot:
                        context.arguments = context.pattern_match.group(2)
                    else:
                        context.arguments = context.pattern_match.group(1)
                except BaseException:
                    analytic = False
                    context.parameter = None
                    context.arguments = None
                await function(context)
                # analytic
                if analytic and allow_analytics:
                    try:
                        upload_command = context.text.split()[0][1:].split("@")[0]
                        upload_command = alias_command(upload_command)
                        if context.sender_id:
                            if context.sender_id > 0:
                                analytics.track(context.sender_id, f'Function {upload_command}',
                                                {'command': upload_command})
                            else:
                                analytics.track(user_id, f'Function {upload_command}',
                                                {'command': upload_command})
                        else:
                            analytics.track(user_id, f'Function {upload_command}',
                                            {'command': upload_command})
                    except Exception as e:
                        logs.info(f"Analytics Error ~ {e}")
            except StopPropagation:
                raise StopPropagation
            except MessageTooLongError:
                await context.edit(lang('too_long'))
            except BaseException as e:
                exc_info = sys.exc_info()[1]
                exc_format = format_exc()
                try:
                    await context.edit(lang('run_error'))
                except BaseException:
                    pass
                if not diagnostics:
                    return
                if strtobool(config['error_report']):
                    report = f"# Generated: {strftime('%H:%M %d/%m/%Y', gmtime())}. \n" \
                             f"# ChatID: {str(context.chat_id)}. \n" \
                             f"# UserID: {str(context.sender_id)}. \n" \
                             f"# Message: \n-----BEGIN TARGET MESSAGE-----\n" \
                             f"{context.text}\n-----END TARGET MESSAGE-----\n" \
                             f"# Traceback: \n-----BEGIN TRACEBACK-----\n" \
                             f"{str(exc_format)}\n-----END TRACEBACK-----\n" \
                             f"# Error: \"{str(exc_info)}\". \n"
                    await attach_report(report, f"exception.{time()}.pagermaid", None,
                                        "Error report generated.")
                    try:
                        sentry_sdk.set_context("Target",
                                               {"ChatID": str(context.chat_id), "UserID": str(context.sender_id),
                                                "Msg": context.text})
                        sentry_sdk.set_tag('com', re.findall("\w+", str.lower(context.text.split()[0]))[0])
                        sentry_sdk.capture_exception(e)
                    except:
                        logs.info(
                            lang('report_error')
                        )

        if not ignore_edited:
            bot.add_event_handler(handler, events.MessageEdited(**args))
        bot.add_event_handler(handler, events.NewMessage(**args))

        return handler

    if not is_plugin and 'disabled_cmd' in config:
        if config['disabled_cmd'].count(command) != 0:
            return noop

    if description is not None and command is not None:
        if parameters is None:
            parameters = ""
        help_messages.update({
            f"{command}": f"**{lang('use_method')}:** `-{command} {parameters}`\
            \n{description}"
        })

    return decorator
