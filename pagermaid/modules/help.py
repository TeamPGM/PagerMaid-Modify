""" The help module. """

from os import listdir
from json import dump as json_dump
from pagermaid import help_messages, alias_dict
from pagermaid.utils import lang, alias_command
from pagermaid.listener import listener, config


@listener(is_plugin=False, outgoing=True, command=alias_command("help"),
          description=lang('help_des'),
          parameters=f"<{lang('command')}>")
async def help_command(context):
    """ The help new command,"""
    support_commands = ['username', 'name', 'pfp', 'bio', 'rmpfp',
                        'profile', 'block', 'unblock', 'ghost', 'deny', 'convert',
                        'caption', 'ocr', 'highlight', 'time', 'translate',
                        'tts', 'google', 'animate',
                        'teletype', 'widen', 'owo', 'flip',
                        'rng', 'aaa', 'tuxsay', 'coin', 'help',
                        'lang', 'alias', 'id', 'uslog', 'log',
                        're', 'leave', 'hitokoto', 'apt', 'prune', 'selfprune',
                        'yourprune', 'del', 'genqr', 'parseqr',
                        'sb', 'sysinfo', 'status',
                        'stats', 'speedtest', 'connection',
                        'pingdc', 'ping', 'topcloud',
                        's', 'sticker', 'sh', 'restart',
                        'trace', 'chat', 'update']
    if context.arguments:
        if context.arguments in help_messages:
            await context.edit(str(help_messages[context.arguments]))
        else:
            await context.edit(lang('arg_error'))
    else:
        result = f"**{lang('help_list')}: \n**"
        for command in sorted(help_messages, reverse=False):
            if str(command) in support_commands:
                continue
            result += "`" + str(command)
            result += "`, "
        if result == f"**{lang('help_list')}: \n**":
            """ The help raw command,"""
            for command in sorted(help_messages, reverse=False):
                result += "`" + str(command)
                result += "`, "
        await context.edit(result[:-2] + f"\n**{lang('help_send')} \"-help <{lang('command')}>\" {lang('help_see')}**\n"
                                         f"[{lang('help_source')}](https://t.me/PagerMaid_Modify) "
                                         f"[{lang('help_plugin')}](https://index.xtaolabs.com/) "
                                         f"[{lang('help_module')}](https://wiki.xtaolabs.com/)")


@listener(is_plugin=False, outgoing=True, command=alias_command("help_raw"),
          description=lang('help_des'),
          parameters=f"<{lang('command')}>")
async def help_raw_command(context):
    """ The help raw command,"""
    if context.arguments:
        if context.arguments in help_messages:
            await context.edit(str(help_messages[context.arguments]))
        else:
            await context.edit(lang('arg_error'))
    else:
        result = f"**{lang('help_list')}: \n**"
        for command in sorted(help_messages, reverse=False):
            result += "`" + str(command)
            result += "`, "
        await context.edit(result[:-2] + f"\n**{lang('help_send')} \"-help <{lang('command')}>\" {lang('help_see')}** "
                                         f"[{lang('help_source')}](https://t.me/PagerMaid_Modify)")


@listener(is_plugin=False, outgoing=True, command=alias_command("lang"),
          description=lang('lang_des'))
async def lang_change(context):
    to_lang = context.arguments
    from_lang = config["application_language"]
    dir, ldir = listdir('languages/built-in'), []
    for i in dir:
        if not i.find('yml') == -1:
            ldir.append(i[:-4])
    with open('config.yml') as f:
        file = f.read()
    if to_lang in ldir:
        file = file.replace(f'application_language: "{from_lang}"', f'application_language: "{to_lang}"')
        with open('config.yml', 'w') as f:
            f.write(file)
        await context.edit(f"{lang('lang_change_to')} {to_lang}, {lang('lang_reboot')}")
        await context.client.disconnect()
    else:
        await context.edit(
            f'{lang("lang_current_lang")} {config["application_language"]}\n\n{lang("lang_all_lang")}{"，".join(ldir)}')


@listener(is_plugin=False, outgoing=True, command="alias",
          description=lang('alias_des'),
          parameters='{list|del|set} <source> <to>')
async def alias_commands(context):
    source_commands = []
    to_commands = []
    texts = []
    for key, value in alias_dict.items():
        source_commands.append(key)
        to_commands.append(value)
    if len(context.parameter) == 0:
        await context.edit(lang('arg_error'))
        return
    elif len(context.parameter) == 1:
        if not len(source_commands) == 0:
            for i in range(0, len(source_commands)):
                texts.append(f'`{source_commands[i]}` --> `{to_commands[i]}`')
            await context.edit(lang('alias_list') + '\n\n' + '\n'.join(texts))
        else:
            await context.edit(lang('alias_no'))
    elif len(context.parameter) == 2:
        source_command = context.parameter[1]
        try:
            del alias_dict[source_command]
            with open("data/alias.json", 'w') as f:
                json_dump(alias_dict, f)
            await context.edit(lang('alias_success'))
            await context.client.disconnect()
        except KeyError:
            await context.edit(lang('alias_no_exist'))
            return
    elif len(context.parameter) == 3:
        source_command = context.parameter[1]
        to_command = context.parameter[2]
        if to_command in help_messages:
            await context.edit(lang('alias_exist'))
            return
        alias_dict[source_command] = to_command
        with open("data/alias.json", 'w') as f:
            json_dump(alias_dict, f)
        await context.edit(lang('alias_success'))
        await context.client.disconnect()
