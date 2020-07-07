""" PagerMaid event listener. """

from telethon import events
from telethon.errors import MessageTooLongError
from distutils2.util import strtobool
from traceback import format_exc
from time import gmtime, strftime, time
from sys import exc_info
from telethon.events import StopPropagation
from pagermaid import bot, config, help_messages
from pagermaid.utils import attach_log
try:
    import sentry_sdk
    from sentry_sdk import capture_message, configure_scope
except:
    pass

def strip_sentry(event, hint):
    return None

def listener(**args):
    """ Register an event listener. """
    command = args.get('command', None)
    description = args.get('description', None)
    parameters = args.get('parameters', None)
    pattern = args.get('pattern', None)
    diagnostics = args.get('diagnostics', True)
    ignore_edited = args.get('ignore_edited', False)
    if command is not None:
        if command in help_messages:
            raise ValueError(f"出错了呜呜呜 ~ 命令 \"{command}\" 已经被注册。")
        pattern = fr"^-{command}(?: |$)([\s\S]*)"
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

    def decorator(function):

        async def handler(context):
            try:
                try:
                    parameter = context.pattern_match.group(1).split(' ')
                    if parameter == ['']:
                        parameter = []
                    context.parameter = parameter
                    context.arguments = context.pattern_match.group(1)
                except BaseException:
                    context.parameter = None
                    context.arguments = None
                await function(context)
            except StopPropagation:
                raise StopPropagation
            except MessageTooLongError:
                await context.edit("出错了呜呜呜 ~ 生成的输出太长，无法显示。")
            except BaseException:
                try:
                    await context.edit("出错了呜呜呜 ~ 执行此命令时发生错误。")
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
                             f"{str(format_exc())}\n-----END TRACEBACK-----\n" \
                             f"# Error: \"{str(exc_info()[1])}\". \n"
                    try:
                        sentry_sdk.init("https://969892b513374f75916aaac1014aa7c2@o416616.ingest.sentry.io/5312335", release="d6f5b9725459f5d0cf96f005bf584d1a7235c405")
                        with configure_scope() as scope:
                            scope.user = eval('{"id": "' + str(context.sender_id) + '"}')
                            scope.set_tag("ChatID", f"{str(context.chat_id)}")
                            scope.level = 'error'
                        capture_message(report)
                        sentry_sdk.init("https://969892b513374f75916aaac1014aa7c2@o416616.ingest.sentry.io/5312335", release="d6f5b9725459f5d0cf96f005bf584d1a7235c405", before_send=strip_sentry)
                    except:
                        pass
                    await attach_log(report, -1001441461877, f"exception.{time()}.pagermaid", None,
                                     "Error report generated.")

        if not ignore_edited:
            bot.add_event_handler(handler, events.MessageEdited(**args))
        bot.add_event_handler(handler, events.NewMessage(**args))

        return handler

    if description is not None and command is not None:
        if parameters is None:
            parameters = ""
        help_messages.update({
            f"{command}": f"**使用方法:** `-{command} {parameters}`\
            \n{description}"
        })

    return decorator
