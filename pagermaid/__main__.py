""" PagerMaid launch sequence. """

from sys import path
from importlib import import_module
from telethon.errors.rpcerrorlist import PhoneNumberInvalidError
from pagermaid import bot, logs, working_dir, user_bot, redis, redis_status
from pagermaid.utils import lang


if not user_bot:
    from pagermaid.modules import module_list, plugin_list
else:
    from pagermaid.bots import module_list, plugin_list

try:
    from pagermaid.interface import server
except TypeError:
    logs.error(lang('web_TypeError'))
    server = None
except KeyError:
    logs.error(lang('web_KeyError'))
    server = None


path.insert(1, f"{working_dir}/plugins")

try:
    bot.start()
except PhoneNumberInvalidError:
    print(lang('PhoneNumberInvalidError'))
    exit(1)

for module_name in module_list:
    try:
        if user_bot:
            import_module("pagermaid.bots." + module_name)
        else:
            import_module("pagermaid.modules." + module_name)
    except BaseException as exception:
        logs.info(f"{lang('module')} {module_name} {lang('error')}: {type(exception)}: {exception}")

for plugin_name in plugin_list:
    try:
        import_module("plugins." + plugin_name)
    except BaseException as exception:
        logs.info(f"{lang('module')} {plugin_name} {lang('error')}: {exception}")
        plugin_list.remove(plugin_name)

if server is not None:
    import_module("pagermaid.interface")

logs.info(lang('start'))

if redis_status():
    async def _restart_complete_report():
        restart_args = redis.get("restart_edit")
        if restart_args:
            redis.delete("restart_edit")
            restart_args = restart_args.decode("utf-8")
            restart_msg, restart_chat = restart_args.split("|")
            await bot.edit_message(
                int(restart_chat), int(restart_msg),
                lang('restart_complete')
            )

    bot.loop.create_task(_restart_complete_report())

bot.run_until_disconnected()

if server is not None:
    try:
        server.stop()
    except AttributeError:
        pass
