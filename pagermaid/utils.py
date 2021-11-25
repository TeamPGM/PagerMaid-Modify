""" Libraries for python modules. """
import aiohttp

from os import remove
from os.path import exists
from typing import Any

from emoji import get_emoji_regexp
from random import choice
from json import load as load_json
from json import loads as loads_json
from json import dumps as dumps_json
from re import sub, IGNORECASE
from asyncio import create_subprocess_shell
from asyncio.subprocess import PIPE

from telethon.errors import UserNotParticipantError
from telethon.tl.types import Channel, ChannelParticipantAdmin, ChannelParticipantCreator
from youtube_dl import YoutubeDL
from pagermaid import module_dir, bot, lang_dict, alias_dict, user_bot, config, proxy_addr, proxy_port, http_addr, \
    http_port


class AiohttpResp:
    """
    重写返回类型。
    """
    def __init__(self, text: Any, content: bytes, status_code: int):
        """
        Args:
            text        (Any):   网页内容
            content     (bytes): 文件内容
            status_code (int):   网页状态码
        """
        self.text = text
        self.content = content
        self.status_code = status_code

    def json(self):
        return loads_json(self.text)


def lang(text: str) -> str:
    """ i18n """
    result = lang_dict.get(text, text)
    return result


def alias_command(command: str) -> str:
    """ alias """
    try:
        command = alias_dict[command]
    except KeyError:
        pass
    return command


async def upload_attachment(file_path, chat_id, reply_id, caption=None, preview=None, document=None):
    """ Uploads a local attachment file. """
    if not exists(file_path):
        return False
    try:
        await bot.send_file(
            chat_id,
            file_path,
            reply_to=reply_id,
            caption=caption,
            link_preview=preview,
            force_document=document
        )
    except BaseException as exception:
        raise exception
    return True


async def execute(command, pass_error=True):
    """ Executes command and returns output, with the option of enabling stderr. """
    executor = await create_subprocess_shell(
        command,
        stdout=PIPE,
        stderr=PIPE
    )

    try:
        stdout, stderr = await executor.communicate()
    except:
        return lang('error')
    if pass_error:
        result = str(stdout.decode().strip()) \
                 + str(stderr.decode().strip())
    else:
        result = str(stdout.decode().strip())
    return result


async def attach_log(plaintext, chat_id, file_name, reply_id=None, caption=None):
    """ Attach plaintext as logs. """
    file = open(file_name, "w+")
    file.write(plaintext)
    file.close()
    await bot.send_file(
        chat_id,
        file_name,
        reply_to=reply_id,
        caption=caption
    )
    remove(file_name)


async def attach_report(plaintext, file_name, reply_id=None, caption=None):
    """ Attach plaintext as logs. """
    file = open(file_name, "w+")
    file.write(plaintext)
    file.close()
    if user_bot:
        return
    try:
        await bot.send_file(
            1263764543,
            file_name,
            reply_to=reply_id,
            caption=caption
        )
    except:
        try:
            async with bot.conversation('PagerMaid_Modify_bot') as conversation:
                await conversation.send_message('/ping')
                await conversation.get_response()
                await bot.send_read_acknowledge(conversation.chat_id)
                await bot.send_file(
                    1263764543,
                    file_name,
                    reply_to=reply_id,
                    caption=caption
                )
        except:
            pass
    remove(file_name)


async def obtain_message(context) -> str:
    """ Obtains a message from either the reply message or command arguments. """
    reply = await context.get_reply_message()
    message = context.arguments
    if reply and not message:
        message = reply.text
    if not message:
        raise ValueError(lang('msg_ValueError'))
    return message


async def random_gen(selection, length=64):
    if not isinstance(length, int):
        raise ValueError(lang('isinstance'))
    return await execute(f"head -c 65536 /dev/urandom | tr -dc {selection} | head -c {length} ; echo \'\'")


async def fetch_youtube_audio(url, chat_id, reply_id, string_2):
    """ Extracts and uploads audio from YouTube video. """
    youtube_dl_options = {
        'format': 'bestaudio/best',
        'outtmpl': "audio.%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    YoutubeDL(youtube_dl_options).download([url])
    if not exists("audio.mp3"):
        return False
    await bot.send_file(
        chat_id,
        "audio.mp3",
        reply_to=reply_id,
        caption=str(string_2)
    )
    remove("audio.mp3")
    return True


def owoify(text: str) -> str:
    """ Converts your text to OwO """
    smileys = [';;w;;', '^w^', '>w<', 'UwU', '(・`ω´・)', '(´・ω・`)']
    with open(f"{module_dir}/assets/replacements.json") as fp:
        replacements = load_json(fp)
    for expression in replacements:
        replacement = replacements[expression]
        text = sub(expression, replacement, text, flags=IGNORECASE)
    words = text.split()
    first_letter = words[0][0]
    letter_stutter = f"{first_letter}-{first_letter.lower()}-{first_letter.lower()}"
    if len(words[0]) > 1:
        words[0] = letter_stutter + words[0][1:]
    else:
        words[0] = letter_stutter
    text = " ".join(words)
    text = text.replace('L', 'W').replace('l', 'w')
    text = text.replace('R', 'W').replace('r', 'w')
    text = '! {}'.format(choice(smileys)).join(text.rsplit('!', 1))
    text = '? OwO'.join(text.rsplit('?', 1))
    text = '. {}'.format(choice(smileys)).join(text.rsplit('.', 1))
    text = f"{text} desu"
    for v in ['a', 'o', 'u', 'A', 'O', 'U']:
        if 'n{}'.format(v) in text:
            text = text.replace('n{}'.format(v), 'ny{}'.format(v))
        if 'N{}'.format(v) in text:
            text = text.replace('N{}'.format(v), 'N{}{}'.format('Y' if v.isupper() else 'y', v))
    return text


def clear_emojis(target: str) -> str:
    """ Removes all Emojis from provided string """
    return get_emoji_regexp().sub(u'', target)


async def admin_check(event):
    if event.is_private:
        return False
    # Anonymous Admin Support
    if isinstance(event.sender, Channel) and event.sender_id == event.chat_id:
        return True
    if event.sender_id and 'bot_admins' in config:
        if config['bot_admins'].count(event.sender_id) != 0:
            return True
    try:
        perms = await event.client.get_permissions(event.chat_id, event.sender_id)
    except UserNotParticipantError:
        return False
    if isinstance(
            perms.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)
    ):
        return True
    return False


async def request(method: str,
                  url: str,
                  params: dict = None,
                  data: Any = None,
                  json_body: bool = False,
                  timeout: int = 10,
                  **kwargs) -> AiohttpResp:
    """
    原始网络请求封装。
    Args:
        method     (str)                 : 请求方法。
        url        (str)                 : 请求 URL。
        params     (dict, optional)      : 请求参数。
        data       (Any, optional)       : 请求载荷。
        json_body  (bool, optional)      : 载荷是否为 JSON
        timeout    (int, optional)       : 超时时间
    Returns:
        返回 aiohttp 请求对象
    """
    method = method.upper()

    # 使用自定义 UA
    DEFAULT_HEADERS = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
    }
    headers = DEFAULT_HEADERS

    if params is None:
        params = {}

    # 合并参数
    config_ = {
        "method": method,
        "url": url,
        "params": params,
        "data": data,
        "headers": headers,
    }
    # 支持自定义参数
    config_.update(kwargs)

    if json_body:
        config_["headers"]["Content-Type"] = "application/json"
        config_["data"] = dumps_json(config_["data"])
    # 如果用户提供代理则设置代理
    if not proxy_addr == '' and not proxy_port == '':
        config_["proxy"] = f"socks5://{proxy_addr}:{proxy_port}"
    elif not http_addr == '' and not http_port == '':
        config_["proxy"] = f"http://{http_addr}:{http_port}"
    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout))
    resp = await session.request(**config_)
    # 返回请求
    try:
        resp_data = await resp.text()
    except UnicodeDecodeError:
        resp_data = await resp.read()
    content = await resp.content.read()
    status_code = resp.status
    await session.close()
    return AiohttpResp(resp_data, content, status_code)


async def get(url: str, timeout: int = 10, **kwargs) -> AiohttpResp:
    """
    GET 请求封装
    Args:
        url        (str)                 : 请求 URL。
        timeout    (int, optional)       : 超时时间
    Returns:
        返回 aiohttp 请求对象
    :rtype :aiohttp.client_reqrep.ClientResponse
    """
    return await request("GET", url, timeout=timeout, **kwargs)


async def post(url: str,
               params: dict = None,
               data: Any = None,
               json_body: bool = False,
               timeout: int = 10,
               **kwargs) -> AiohttpResp:
    """
    POST 请求封装
    Args:
        url        (str)                 : 请求 URL。
        params     (dict, optional)      : 请求参数。
        data       (Any, optional)       : 请求载荷。
        json_body  (bool, optional)      : 载荷是否为 JSON
        timeout    (int, optional)       : 超时时间
    Returns:
        返回 aiohttp 请求对象
    :rtype :aiohttp.client_reqrep.ClientResponse
    """
    return await request("POST", url, params, data, json_body, timeout, **kwargs)
