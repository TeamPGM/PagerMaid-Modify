""" PagerMaid module that contains utilities related to system status. """

from json import loads
from PIL import Image
from requests import get
from os import remove, popen
from datetime import datetime
from speedtest import distance, Speedtest, ShareResultsConnectFailure, ShareResultsSubmitFailure, NoMatchedServers, \
    SpeedtestBestServerFailure, SpeedtestHTTPError
from telethon import functions
from platform import python_version, uname
from wordcloud import WordCloud
from telethon import version as telethon_version
from telethon.tl.types import User, Chat, Channel
from sys import platform
from re import sub, findall
from pathlib import Path
from pagermaid import log, config, redis_status, start_time
from pagermaid.utils import execute, upload_attachment
from pagermaid.listener import listener
from pagermaid.utils import lang, alias_command

DCs = {
    1: "149.154.175.50",
    2: "149.154.167.51",
    3: "149.154.175.100",
    4: "149.154.167.91",
    5: "91.108.56.130"
}


@listener(is_plugin=False, outgoing=True, command=alias_command("sysinfo"),
          description=lang('sysinfo_des'))
async def sysinfo(context):
    """ Retrieve system information via neofetch. """
    await context.edit(lang('sysinfo_loading'))
    result = await execute("neofetch --config none --stdout")
    await context.edit(f"`{result}`")


@listener(is_plugin=False, outgoing=True, command=alias_command("fortune"),
          description=lang('fortune_des'))
async def fortune(context):
    """ Reads a fortune cookie. """
    result = await execute("fortune")
    if result == "/bin/sh: fortune: command not found":
        await context.edit(lang('fortune_not_exist'))
        return
    await context.edit(result)


@listener(is_plugin=False, outgoing=True, command=alias_command("fbcon"),
          description=lang('fbcon_des'))
async def tty(context):
    """ Screenshots a TTY and prints it. """
    await context.edit(lang('fbcon_processing'))
    reply_id = context.message.reply_to_msg_id
    result = await execute("fbdump | convert - image.png")
    if result == "/bin/sh: fbdump: command not found":
        await context.edit(lang('fbcon_no_fbdump'))
        remove("image.png")
        return
    if result == "/bin/sh: convert: command not found":
        await context.edit(lang('fbcon_no_ImageMagick'))
        remove("image.png")
        return
    if result == "Failed to open /dev/fb0: Permission denied":
        await context.edit(lang('fbcon_no_permission'))
        return
    if not await upload_attachment("./image.png", context.chat_id, reply_id,
                                   caption=lang('fbcon_caption'),
                                   preview=False, document=False):
        await context.edit(lang('fbcon_error'))
        return
    await context.delete()
    try:
        remove("./image.png")
    except:
        pass
    await log("Screenshot of binded framebuffer console taken.")


@listener(is_plugin=False, outgoing=True, command=alias_command("status"),
          description=lang('status_des'))
async def status(context):
    # database
    database = lang('status_online') if redis_status() else lang('status_offline')
    # uptime https://gist.github.com/borgstrom/936ca741e885a1438c374824efb038b3
    time_units = (
        ('%m', 60 * 60 * 24 * 30),
        ('%d', 60 * 60 * 24),
        ('%H', 60 * 60),
        ('%M', 60),
        ('%S', 1)
    )

    async def human_time_duration(seconds):
        parts = {}
        for unit, div in time_units:
            amount, seconds = divmod(int(seconds), div)
            parts[unit] = str(amount)
        try:
            time_form = config['start_form']
        except (ValueError, KeyError):
            time_form = "%m/%d %H:%M"
        for key, value in parts.items():
            time_form = time_form.replace(key, value)
        return time_form

    current_time = datetime.utcnow()
    uptime_sec = (current_time - start_time).total_seconds()
    uptime = await human_time_duration(int(uptime_sec))
    text = (f"**{lang('status_hint')}** \n"
            f"{lang('status_name')}: `{uname().node}` \n"
            f"{lang('status_platform')}: `{platform}` \n"
            f"{lang('status_release')}: `{uname().release}` \n"
            f"{lang('status_python')}: `{python_version()}` \n"
            f"{lang('status_telethon')}: `{telethon_version.__version__}` \n"
            f"{lang('status_db')}: `{database}` \n"
            f"{lang('status_uptime')}: `{uptime}`"
            )
    await context.edit(text)


@listener(is_plugin=False, outgoing=True, command=alias_command("stats"),
          description=lang('stats_des'))
async def stats(context):
    await context.edit(lang('stats_loading'))
    u, g, s, c, b = 0, 0, 0, 0, 0
    dialogs = await context.client.get_dialogs(
        limit=None,
        ignore_migrated=True
    )
    for d in dialogs:
        current_entity = d.entity
        if type(current_entity) is User:
            if current_entity.bot:
                b += 1
            else:
                u += 1
        elif type(current_entity) is Chat:
            g += 1
        elif type(current_entity) is Channel:
            if current_entity.broadcast:
                c += 1
            else:
                s += 1
    text = (f"**{lang('stats_hint')}** \n"
            f"{lang('stats_dialogs')}: `{len(dialogs)}` \n"
            f"{lang('stats_private')}: `{u}` \n"
            f"{lang('stats_group')}: `{g}` \n"
            f"{lang('stats_supergroup')}: `{s}` \n"
            f"{lang('stats_channel')}: `{c}` \n"
            f"{lang('stats_bot')}: `{b}`"
            )
    await context.edit(text)


@listener(is_plugin=False, outgoing=True, command=alias_command("speedtest"),
          description=lang('speedtest_des'))
async def speedtest(context):
    """ Tests internet speed using speedtest. """
    try:
        speed_test_path = config['speed_test_path']
    except KeyError:
        speed_test_path = ''
    if not speed_test_path == '':
        server = None
        if len(context.parameter) == 1:
            try:
                server = int(context.parameter[0])
            except ValueError:
                await context.edit(lang('arg_error'))
                return
        speed_test_path += ' -f json'
        if server:
            speed_test_path += f' -s {server}'
        await context.edit(lang('speedtest_processing'))
        result = await execute(f'{speed_test_path}')
        result = loads(result)
        if result['type'] == 'log':
            await context.edit(f"{result['level'].upper()}:{result['message']}")
        elif result['type'] == 'result':
            des = (
                f"**Speedtest** \n"
                f"Server: `{result['server']['name']} - "
                f"{result['server']['location']}` \n"
                f"Host: `{result['server']['host']}` \n"
                f"Upload: `{unit_convert(result['upload']['bandwidth'] * 8)}` \n"
                f"Download: `{unit_convert(result['download']['bandwidth'] * 8)}` \n"
                f"Latency: `{result['ping']['latency']}` \n"
                f"Jitter: `{result['ping']['jitter']}` \n"
                f"Timestamp: `{result['timestamp']}`"
            )
            # 开始处理图片
            data = get(f"{result['result']['url']}.png").content
            with open('speedtest.png', mode='wb') as f:
                f.write(data)
            try:
                img = Image.open('speedtest.png')
                c = img.crop((17, 11, 727, 389))
                c.save('speedtest.png')
            except:
                pass
            try:
                await context.client.send_file(context.chat_id, 'speedtest.png', caption=des)
            except:
                pass
            try:
                remove('speedtest.png')
            except:
                pass
            await context.delete()
        else:
            await context.edit(result)
        return
    try:
        test = Speedtest()
    except SpeedtestHTTPError:
        await context.edit(lang('speedtest_ConnectFailure'))
        return
    server, server_json = [], False
    if len(context.parameter) == 1:
        try:
            server = [int(context.parameter[0])]
        except ValueError:
            await context.edit(lang('arg_error'))
            return
    elif len(context.parameter) >= 2:
        try:
            temp_json = findall(r'{(.*?)}', context.text.replace("'", '"'))
            if len(temp_json) == 1:
                server_json = loads("{" + temp_json[0] + "}")
                server_json['d'] = distance(test.lat_lon, (float(server_json['lat']), float(server_json['lon'])))
                test.servers = [server_json]
            else:
                await context.edit(lang('arg_error'))
                return
        except:
            pass
    await context.edit(lang('speedtest_processing'))
    try:
        if len(server) == 0:
            if not server_json:
                test.get_best_server()
            else:
                test.get_best_server(servers=test.servers)
        else:
            test.get_servers(servers=server)
    except (SpeedtestBestServerFailure, NoMatchedServers) as e:
        await context.edit(lang('speedtest_ServerFailure'))
        return
    try:
        test.download()
        test.upload()
        test.results.share()
    except (ShareResultsConnectFailure, ShareResultsSubmitFailure, RuntimeError) as e:
        await context.edit(lang('speedtest_ConnectFailure'))
        return
    result = test.results.dict()
    des = (
        f"**Speedtest** \n"
        f"Server: `{result['server']['name']} - "
        f"{result['server']['cc']}` \n"
        f"Sponsor: `{result['server']['sponsor']}` \n"
        f"Upload: `{unit_convert(result['upload'])}` \n"
        f"Download: `{unit_convert(result['download'])}` \n"
        f"Latency: `{result['ping']}` \n"
        f"Timestamp: `{result['timestamp']}`"
    )
    # 开始处理图片
    data = get(result['share']).content
    with open('speedtest.png', mode='wb') as f:
        f.write(data)
    try:
        img = Image.open('speedtest.png')
        c = img.crop((17, 11, 727, 389))
        c.save('speedtest.png')
    except:
        pass
    try:
        await context.client.send_file(context.chat_id, 'speedtest.png', caption=des)
    except:
        return
    try:
        remove('speedtest.png')
    except:
        pass
    await context.delete()


@listener(is_plugin=False, outgoing=True, command=alias_command("connection"),
          description=lang('connection_des'))
async def connection(context):
    """ Displays connection information between PagerMaid and Telegram. """
    datacenter = await context.client(functions.help.GetNearestDcRequest())
    await context.edit(
        f"**{lang('connection_hint')}** \n"
        f"{lang('connection_country')}: `{datacenter.country}` \n"
        f"{lang('connection_dc')}: `{datacenter.this_dc}` \n"
        f"{lang('connection_nearest_dc')}: `{datacenter.nearest_dc}`"
    )


@listener(is_plugin=False, outgoing=True, command=alias_command("pingdc"),
          description=lang('pingdc_des'))
async def pingdc(context):
    """ Ping your or other data center's IP addresses. """
    data = []
    for dc in range(1, 6):
        result = await execute(f"ping -c 1 {DCs[dc]} | awk -F '/' " + "'END {print $5}'")
        data.append(result)
    await context.edit(
        f"{lang('pingdc_1')}: `{data[0]}ms`\n"
        f"{lang('pingdc_2')}: `{data[1]}ms`\n"
        f"{lang('pingdc_3')}: `{data[2]}ms`\n"
        f"{lang('pingdc_4')}: `{data[3]}ms`\n"
        f"{lang('pingdc_5')}: `{data[4]}ms`"
    )


@listener(is_plugin=False, outgoing=True, command=alias_command("ping"),
          description=lang('ping_des'))
async def ping(context):
    """ Calculates latency between PagerMaid and Telegram. """
    start = datetime.now()
    await context.edit("Pong!")
    end = datetime.now()
    duration = (end - start).microseconds / 1000
    await context.edit(f"Pong!|{duration}")


@listener(is_plugin=False, outgoing=True, command=alias_command("topcloud"),
          description=lang('topcloud_des'))
async def topcloud(context):
    """ Generates a word cloud of resource-hungry processes. """
    await context.edit(lang('topcloud_processing'))
    command_list = []
    if not Path('/usr/bin/top').is_symlink():
        output = str(await execute("top -b -n 1")).split("\n")[7:]
    else:
        output = str(await execute("top -b -n 1")).split("\n")[4:]
    for line in output[:-1]:
        line = sub(r'\s+', ' ', line).strip()
        fields = line.split(" ")
        try:
            if fields[11].count("/") > 0:
                command = fields[11].split("/")[0]
            else:
                command = fields[11]

            cpu = float(fields[8].replace(",", "."))
            mem = float(fields[9].replace(",", "."))

            if command != "top":
                command_list.append((command, cpu, mem))
        except BaseException:
            pass
    command_dict = {}
    for command, cpu, mem in command_list:
        if command in command_dict:
            command_dict[command][0] += cpu
            command_dict[command][1] += mem
        else:
            command_dict[command] = [cpu + 1, mem + 1]

    resource_dict = {}

    for command, [cpu, mem] in command_dict.items():
        resource_dict[command] = (cpu ** 2 + mem ** 2) ** 0.5

    width, height = None, None
    try:
        width, height = ((popen("xrandr | grep '*'").read()).split()[0]).split("x")
        width = int(width)
        height = int(height)
    except BaseException:
        pass
    if not width or not height:
        width = int(config['width'])
        height = int(config['height'])
    background = config['background']
    margin = int(config['margin'])

    try:
        cloud = WordCloud(
            background_color=background,
            width=width - 2 * int(margin),
            height=height - 2 * int(margin)
        ).generate_from_frequencies(resource_dict)
    except ValueError:
        await context.edit(lang('run_error'))
        return

    cloud.to_file("cloud.png")
    await context.edit(lang('highlight_uploading'))
    await context.client.send_file(
        context.chat_id,
        "cloud.png",
        reply_to=None,
        caption=lang('topcloud_caption')
    )
    remove("cloud.png")
    await context.delete()
    await log(lang('topcloud_success'))


def unit_convert(byte):
    """ Converts byte into readable formats. """
    power = 1000
    zero = 0
    units = {
        0: '',
        1: 'Kb/s',
        2: 'Mb/s',
        3: 'Gb/s',
        4: 'Tb/s'}
    while byte > power:
        byte /= power
        zero += 1
    return f"{round(byte, 2)} {units[zero]}"
