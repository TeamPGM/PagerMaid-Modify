""" Send Msg At A Specified Time. """

# By tg @fruitymelon
# extra requirements: dateparser

imported = True

import os, sys, time, traceback

try:
    import dateparser
except ImportError:
    imported = False

import asyncio
from pagermaid import log 
from pagermaid.listener import listener
from datetime import datetime
from dateutil import parser


def logsync(message):
    sys.stdout.writelines(f"{message}\n")

logsync("sendat: loading... If failed, please install dateparser first.")

# https://stackoverflow.com/questions/1111056/get-time-zone-information-of-the-system-in-python
def local_time_offset(t=None):
    """Return offset of local zone from GMT, either at present or at time t."""
    # python2.3 localtime() can't take None
    if t is None:
        t = time.time()

    if time.localtime(t).tm_isdst and time.daylight:
        return -time.altzone
    else:
        return -time.timezone

offset = local_time_offset() // 3600
sign = "+" if offset >= 0 else "-"
offset = abs(offset)
offset_str = str(offset)
offset_str = offset_str if len(offset_str) == 2 else f"0{offset_str}"

settings = {'TIMEZONE': f'{sign}{offset_str}00'}

logsync(f"sendat: local time zone offset is {sign}{abs(offset)}")


helpmsg = """
定时发送消息。
-sendat 时间 | 消息内容

i.e.
-sendat 16:00:00 | 投票截止！
-sendat every 23:59:59 | 又是无所事事的一天呢。
-sendat every 1 minutes | 又过去了一分钟。
-sendat *3 1 minutes | 此消息将出现三次，间隔均为一分钟。
"""

@listener(outgoing=True, command="sendat", diagnostics=True, ignore_edited=False,
          description=helpmsg,
          parameters="<atmsg>")
async def sendat(context):
    args = " ".join(context.parameter).split("|")
    chat = await context.get_chat()
    if not imported:
        await context.edit("Please install dateparser first: python3 -m pip install dateparser")
        return
    await context.edit(f"tz data: {time.timezone} {time.tzname} {sign}{offset}")
    if len(args) != 2:
        await context.edit("Invalid argument. Expected: 2")
        return
    if offset is None:
        await context.edit("Failed to get server timezone.")
        return
    try:
        if args[0].find("every ") == 0:
            # at this point, let's assume args[0] contains relative time
            # i.e. -sendat every 3 minutes
            time_str = args[0][6:]
            if time_str.find(":") != -1:
                # then it should be absolute time
                sleep_times = [abs(dateparser.parse(time_str, settings=settings).timestamp() - time.time()), 24 * 60 * 60]
                index = 0
                await context.edit(f"Registered.")
                while True:
                    last_time = time.time()
                    while time.time() < last_time + sleep_times[index]:
                        await asyncio.sleep(2)
                    await sendmsg(context, chat, args[1])
                    index = 1
                return
            sleep_time = abs(dateparser.parse(time_str, settings=settings).timestamp() - time.time())
            if sleep_time < 5:
                await context.edit(f"Sleep time too short. Should be longer than 5 seconds. Got {sleep_time}") 
                return
            await context.edit(f"Registered.")
            while True:
                last_time = time.time()
                while time.time() < last_time + sleep_time:
                    await asyncio.sleep(2)
                await sendmsg(context, chat, args[1])
            return
        elif args[0].find("*") == 0:
            times = int(args[0][1:].split(" ")[0])
            rest = " ".join(args[0][1:].split(" ")[1:])
            if rest.find(":") != -1:
                # then it should be absolute time
                sleep_times = [abs(dateparser.parse(rest, settings=settings).timestamp() - time.time()), 24 * 60 * 60]
                count = 0
                await context.edit("Registered.")
                while count <= times:
                    last_time = time.time()
                    while time.time() < last_time + sleep_times[0 if count == 0 else 1]:
                        await asyncio.sleep(2)
                    await sendmsg(context, chat, args[1])
                    count += 1
                return
            sleep_time = abs(dateparser.parse(rest, settings=settings).timestamp() - time.time())
            if sleep_time < 5:
                await context.edit("Sleep time too short. Should be longer than 5 seconds.")
                return
            count = 0
            await context.edit("Registered.")
            while count <= times:
                last_time = time.time()
                while time.time() < last_time + sleep_time:
                    await asyncio.sleep(2)
                await sendmsg(context, chat, args[1])
                count += 1
            return
        
        # absolute time
        dt = parser.parse(args[0])
        delta = dt.timestamp() - time.time()
        if delta < 3:
            await context.edit("Target time before now.")
            return
        await context.edit("Registered.")
        while delta > 0:
            delta = dt.timestamp() - time.time()
            await asyncio.sleep(2)
        await sendmsg(context, chat, args[1])
    except Exception as e:
        await log(str(e))
        await log(str(traceback.format_stack()))
        return


async def sendmsg(context, chat, text):
    await context.client.send_message(chat, text)

