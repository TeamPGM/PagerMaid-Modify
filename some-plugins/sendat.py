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

mem = []

helpmsg = """
定时发送消息。
-sendat 时间 | 消息内容

i.e.
-sendat 16:00:00 | 投票截止！
-sendat every 23:59:59 | 又是无所事事的一天呢。
-sendat every 1 minutes | 又过去了一分钟。
-sendat *3 1 minutes | 此消息将出现三次，间隔均为一分钟。

此命令可与 autorespond, ghost, deny 命令串联：

-sendat 10 minutes | -autorespond 我暂时有事离开一下。
"""

@listener(outgoing=True, command="sendat", diagnostics=True, ignore_edited=False,
          description=helpmsg,
          parameters="<atmsg>")
async def sendatwrap(context):
    await sendat(context)

async def sendat(context):
    mem_id = len(mem)
    chat = await context.get_chat()
    args = " ".join(context.parameter).split("|")
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
                mem.append("|".join(args))
                await context.edit(f"Registered: id {mem_id}")
                while True:
                    last_time = time.time()
                    while time.time() < last_time + sleep_times[index]:
                        await asyncio.sleep(2)
                    await sendmsg(context, chat, args[1])
                    index = 1
                mem[mem_id] = ""
                return
            sleep_time = abs(dateparser.parse(time_str, settings=settings).timestamp() - time.time())
            if sleep_time < 5:
                await context.edit(f"Sleep time too short. Should be longer than 5 seconds. Got {sleep_time}") 
                return
            mem.append("|".join(args))
            await context.edit(f"Registered: id {mem_id}")
            while True:
                last_time = time.time()
                while time.time() < last_time + sleep_time:
                    await asyncio.sleep(2)
                await sendmsg(context, chat, args[1])
            mem[mem_id] = ""
            return
        elif args[0].find("*") == 0:
            times = int(args[0][1:].split(" ")[0])
            rest = " ".join(args[0][1:].split(" ")[1:])
            if rest.find(":") != -1:
                # then it should be absolute time
                sleep_times = [abs(dateparser.parse(rest, settings=settings).timestamp() - time.time()), 24 * 60 * 60]
                count = 0
                mem.append("|".join(args))
                await context.edit(f"Registered: id {mem_id}")
                while count <= times:
                    last_time = time.time()
                    while time.time() < last_time + sleep_times[0 if count == 0 else 1]:
                        await asyncio.sleep(2)
                    await sendmsg(context, chat, args[1])
                    count += 1
                mem[mem_id] = ""
                return
            sleep_time = abs(dateparser.parse(rest, settings=settings).timestamp() - time.time())
            if sleep_time < 5:
                await context.edit("Sleep time too short. Should be longer than 5 seconds.")
                return
            count = 0
            mem.append("|".join(args))
            await context.edit(f"Registered: id {mem_id}")
            while count <= times:
                last_time = time.time()
                while time.time() < last_time + sleep_time:
                    await asyncio.sleep(2)
                await sendmsg(context, chat, args[1])
                count += 1
            mem[mem_id] = ""
            return

        if args[0].find(":") == -1:
            # relative time
            dt = dateparser.parse(args[0])
            delta = time.time() - dt.timestamp()
            if delta < 3:
                await context.edit("Target time before now.")
                return
            mem.append("|".join(args))
            await context.edit(f"Registered: id {mem_id}")
            while dt.timestamp() + 2*delta > time.time():
                await asyncio.sleep(2)
            await sendmsg(context, chat, args[1])
            mem[mem_id] = ""
            return

        # absolute time
        dt = parser.parse(args[0])
        delta = dt.timestamp() - time.time()
        if delta < 3:
            await context.edit("Target time before now.")
            return
        mem.append("|".join(args))
        await context.edit(f"Registered: id {mem_id}")
        while delta > 0:
            delta = dt.timestamp() - time.time()
            await asyncio.sleep(2)
        await sendmsg(context, chat, args[1])
        mem[mem_id] = ""
    except Exception as e:
        await log(str(e))
        await log(str(traceback.format_stack()))
        return


@listener(outgoing=True, command="sendatdump", diagnostics=True, ignore_edited=False,
          description="导出 sendat 消息")
async def sendatdump(context):
    if mem.count("") != 0:
        await context.edit(".\n-sendat " + "\n-sendat ".join(mem[:].remove("")))
    else:
        await context.edit(".\n-sendat " + "\n-sendat ".join(mem))

@listener(outgoing=True, command="sendatparse", diagnostics=True, ignore_edited=True,
          description="导入已导出的 sendat 消息")
async def sendatparse(context):
    chat = await context.get_chat()
    text = "\n".join(context.message.text.split("\n")[1:])
    if text == "":
        return
    if text.find(".\n") == 0:
        text = "\n".join(text.split("\n")[1:])
    lines = text.split("\n")
    for i in range(len(lines)):
        line = lines[i]
        sent = await sendmsg(context, chat, line)
        sent.parameter = line.replace("-sendat ", "").split(" ")
        await sendat(sent)

""" Modified pagermaid autorespond plugin. """

from telethon.events import StopPropagation
from pagermaid import persistent_vars

async def autorespond(context):
    """ Enables the auto responder. """
    message = "我还在睡觉... ZzZzZzZzZZz"
    if context.arguments:
        message = context.arguments
    await context.edit("成功启用自动响应器。")
    await log(f"启用自动响应器，将自动回复 `{message}`.")
    persistent_vars.update({'autorespond': {'enabled': True, 'message': message, 'amount': 0}})

from pagermaid import redis, redis_status

async def ghost(context):
    """ Toggles ghosting of a user. """
    if not redis_status():
        await context.edit("出错了呜呜呜 ~ Redis 好像离线了，无法执行命令。")
        return
    if len(context.parameter) != 1:
        await context.edit("出错了呜呜呜 ~ 无效的参数。")
        return
    myself = await context.client.get_me()
    self_user_id = myself.id
    if context.parameter[0] == "true":
        if context.chat_id == self_user_id:
            await context.edit("在？为什么要在收藏夹里面用？")
            return
        redis.set("ghosted.chat_id." + str(context.chat_id), "true")
        await context.delete()
        await log(f"已成功将 ChatID {str(context.chat_id)} 添加到自动已读对话列表中。")
    elif context.parameter[0] == "false":
        if context.chat_id == self_user_id:
            await context.edit("在？为什么要在收藏夹里面用？")
            return
        redis.delete("ghosted.chat_id." + str(context.chat_id))
        await context.delete()
        await log(f"已成功将 ChatID {str(context.chat_id)} 从自动已读对话列表中移除。")
    elif context.parameter[0] == "status":
        if redis.get("ghosted.chat_id." + str(context.chat_id)):
            await context.edit("emm...当前对话已被加入自动已读对话列表中。")
        else:
            await context.edit("emm...当前对话已从自动已读对话列表中移除。")
    else:
        await context.edit("出错了呜呜呜 ~ 无效的参数。")


async def deny(context):
    """ Toggles denying of a user. """
    if not redis_status():
        await context.edit("出错了呜呜呜 ~ Redis 离线，无法运行。")
        return
    if len(context.parameter) != 1:
        await context.edit("出错了呜呜呜 ~ 无效的参数。")
        return
    myself = await context.client.get_me()
    self_user_id = myself.id
    if context.parameter[0] == "true":
        if context.chat_id == self_user_id:
            await context.edit("在？为什么要在收藏夹里面用？")
            return
        redis.set("denied.chat_id." + str(context.chat_id), "true")
        await context.delete()
        await log(f"ChatID {str(context.chat_id)} 已被添加到自动拒绝对话列表中。")
    elif context.parameter[0] == "false":
        if context.chat_id == self_user_id:
            await context.edit("在？为什么要在收藏夹里面用？")
            return
        redis.delete("denied.chat_id." + str(context.chat_id))
        await context.delete()
        await log(f"ChatID {str(context.chat_id)} 已从自动拒绝对话列表中移除。")
    elif context.parameter[0] == "status":
        if redis.get("denied.chat_id." + str(context.chat_id)):
            await context.edit("emm...当前对话已被加入自动拒绝对话列表中。")
        else:
            await context.edit("emm...当前对话已从自动拒绝对话列表移除。")
    else:
        await context.edit("出错了呜呜呜 ~ 无效的参数。")


async def sendmsg(context, chat, origin_text):
    text = origin_text.strip()
    msg = await context.client.send_message(chat, text)
    if text.find("-autorespond") == 0:
        msg.arguments = text.replace("-autorespond", "").lstrip()
        await autorespond(msg)
    elif text.find("-ghost ") == 0:
        msg.parameter = [text[7:]]
        await ghost(msg)
    elif text.find("-deny ") == 0:
        msg.parameter = [text[6:]]
        await deny(msg)
    return msg
