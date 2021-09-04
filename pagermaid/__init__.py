""" PagerMaid initialization. """

from concurrent.futures import CancelledError

# Analytics
import sentry_sdk
from sentry_sdk.integrations.redis import RedisIntegration

python36 = True
try:
    from asyncio.exceptions import CancelledError as CancelError

    python36 = False
except:
    pass
from subprocess import run, PIPE
from datetime import datetime
from time import time
from os import getcwd, makedirs, environ
from os.path import exists
from sys import version_info, platform
from yaml import load, FullLoader, safe_load
from json import load as load_json
from shutil import copyfile
from redis import StrictRedis
from logging import getLogger, INFO, DEBUG, ERROR, StreamHandler, basicConfig
from distutils.util import strtobool
from coloredlogs import ColoredFormatter
from telethon import TelegramClient
from telethon.sessions import StringSession

# Errors
from telethon.errors.rpcerrorlist import MessageNotModifiedError, MessageIdInvalidError, ChannelPrivateError, \
    ChatSendMediaForbiddenError, YouBlockedUserError, FloodWaitError, ChatWriteForbiddenError, \
    AuthKeyDuplicatedError, ChatSendStickersForbiddenError, SlowModeWaitError, MessageEditTimeExpiredError, \
    PeerIdInvalidError
from telethon.errors.common import AlreadyInConversationError
from requests.exceptions import ChunkedEncodingError
from requests.exceptions import ConnectionError as ConnectedError
from sqlite3 import OperationalError
from http.client import RemoteDisconnected
from urllib.error import URLError
from concurrent.futures._base import TimeoutError
from redis.exceptions import ResponseError

persistent_vars = {}
module_dir = __path__[0]
working_dir = getcwd()
config = None
help_messages = {}
logs = getLogger(__name__)
logging_format = "%(levelname)s [%(asctime)s] [%(name)s] %(message)s"
logging_handler = StreamHandler()
logging_handler.setFormatter(ColoredFormatter(logging_format))
root_logger = getLogger()
root_logger.setLevel(ERROR)
root_logger.addHandler(logging_handler)
basicConfig(level=INFO)
logs.setLevel(INFO)

try:
    config = load(open(r"config.yml"), Loader=FullLoader)
except FileNotFoundError:
    logs.fatal("The configuration file does not exist, and a new configuration file is being generated.")
    copyfile(f"{module_dir}/assets/config.gen.yml", "config.yml")
    exit(1)

# i18n
lang_dict: dict = {}

try:
    with open(f"languages/built-in/{config['application_language']}.yml", "r", encoding="utf-8") as f:
        lang_dict = safe_load(f)
except Exception as e:
    print("Reading language YAML file failed")
    print(e)
    exit(1)
# Customization
try:
    with open(f"languages/custom.yml", "r", encoding="utf-8") as f:
        lang_temp = safe_load(f)
    for key, value in lang_temp.items():
        lang_dict[key] = value
except FileNotFoundError:
    pass
except Exception as e:
    logs.fatal("Reading custom YAML file failed")

# alias
alias_dict: dict = {}

if exists("data/alias.json"):
    try:
        with open("data/alias.json", encoding="utf-8") as f:
            alias_dict = load_json(f)
    except Exception as e:
        print("Reading alias file failed")
        print(e)
        exit(1)


def lang(text: str) -> str:
    """ i18n """
    result = lang_dict.get(text, text)
    return result


analytics = None
try:
    allow_analytics = strtobool(config['allow_analytic'])
except KeyError:
    allow_analytics = True
except ValueError:
    allow_analytics = True
if allow_analytics:
    import analytics

    analytics.write_key = 'EI5EyxFl8huwAvv932Au7XoRSdZ63wC4'
    analytics = analytics
if strtobool(config['debug']):
    logs.setLevel(DEBUG)
else:
    logs.setLevel(INFO)

if platform == "linux" or platform == "linux2" or platform == "darwin" or platform == "freebsd7" \
        or platform == "freebsd8" or platform == "freebsdN" or platform == "openbsd6":
    logs.info(
        lang('platform') + platform + lang('platform_load')
    )
else:
    logs.error(
        f"{lang('error_prefix')} {lang('platform')}" + platform + lang('platform_unsupported')
    )
    exit(1)

if version_info[0] < 3 or version_info[1] < 6:
    logs.error(
        f"{lang('error_prefix')} {lang('python')}"
    )
    exit(1)

if not exists(f"{getcwd()}/data"):
    makedirs(f"{getcwd()}/data")

api_key = config['api_key']
api_hash = config['api_hash']
session_string = "pagermaid"
# environ
if environ.get('api_key'):
    api_key = environ.get('api_key')
if environ.get('api_hash'):
    api_hash = environ.get('api_hash')
if environ.get('session'):
    string_session = environ.get('session')
    session_string = StringSession(string_session)
# api type
try:
    api_key = int(api_key)
except ValueError:
    logs.info(
        lang('config_error')
    )
    exit(1)
except:
    pass
try:
    proxy_addr = config['proxy_addr'].strip()
    proxy_port = config['proxy_port'].strip()
    http_addr = config['http_addr'].strip()
    http_port = config['http_port'].strip()
    mtp_addr = config['mtp_addr'].strip()
    mtp_port = config['mtp_port'].strip()
    mtp_secret = config['mtp_secret'].strip()
except KeyError:
    proxy_addr = ''
    proxy_port = ''
    http_addr = ''
    http_port = ''
    mtp_addr = ''
    mtp_port = ''
    mtp_secret = ''
try:
    redis_host = config['redis']['host']
except KeyError:
    redis_host = 'localhost'
try:
    redis_port = config['redis']['port']
except KeyError:
    redis_port = 6379
try:
    redis_db = config['redis']['db']
except KeyError:
    redis_db = 14
try:
    if strtobool(config['ipv6']):
        use_ipv6 = True
    else:
        use_ipv6 = False
except KeyError:
    use_ipv6 = False
if api_key is None or api_hash is None:
    logs.info(
        lang('config_error')
    )
    exit(1)

# 开始检查代理配置
proxies = {}
if not proxy_addr == '' and not proxy_port == '':
    try:
        import python_socks

        proxies = {
            "http": f"socks5://{proxy_addr}:{proxy_port}",
            "https": f"socks5://{proxy_addr}:{proxy_port}"
        }
        bot = TelegramClient(session_string, api_key, api_hash,
                             auto_reconnect=True,
                             proxy=(python_socks.ProxyType.SOCKS5, proxy_addr, int(proxy_port)),
                             use_ipv6=use_ipv6)
    except:
        proxies = {}
        bot = TelegramClient(session_string, api_key, api_hash,
                             auto_reconnect=True,
                             use_ipv6=use_ipv6)
elif not http_addr == '' and not http_port == '':
    try:
        import python_socks

        proxies = {
            "http": f"http://{http_addr}:{http_port}",
            "https": f"http://{http_addr}:{http_port}"
        }
        bot = TelegramClient(session_string, api_key, api_hash,
                             auto_reconnect=True,
                             proxy=(python_socks.ProxyType.HTTP, http_addr, int(http_port)),
                             use_ipv6=use_ipv6)
    except:
        bot = TelegramClient(session_string, api_key, api_hash,
                             auto_reconnect=True,
                             use_ipv6=use_ipv6)
elif not mtp_addr == '' and not mtp_port == '' and not mtp_secret == '':
    from telethon import connection

    bot = TelegramClient(session_string, api_key, api_hash,
                         auto_reconnect=True,
                         connection=connection.ConnectionTcpMTProxyRandomizedIntermediate,
                         proxy=(mtp_addr, int(mtp_port), mtp_secret),
                         use_ipv6=use_ipv6)
else:
    bot = TelegramClient(session_string, api_key, api_hash, auto_reconnect=True, use_ipv6=use_ipv6)
user_id = 0
redis = StrictRedis(host=redis_host, port=redis_port, db=redis_db)


async def save_id():
    global user_id
    me = await bot.get_me()
    user_id = me.id
    if me.username is not None:
        sentry_sdk.set_user({"id": user_id, "name": me.first_name, "username": me.username, "ip_address": "{{auto}}"})
        if allow_analytics:
            analytics.identify(user_id, {
                'name': me.first_name,
                'username': me.username
            })
    else:
        sentry_sdk.set_user({"id": user_id, "name": me.first_name, "ip_address": "{{auto}}"})
        if allow_analytics:
            analytics.identify(user_id, {
                'name': me.first_name
            })
    logs.info(f"{lang('save_id')} {me.first_name}({user_id})")


with bot:
    bot.loop.run_until_complete(save_id())


def before_send(event, hint):
    global report_time
    exc_info = hint.get("exc_info")
    if exc_info and isinstance(exc_info[1], ConnectionError):
        return
    elif exc_info and isinstance(exc_info[1], CancelledError):
        return
    elif exc_info and isinstance(exc_info[1], MessageNotModifiedError):
        return
    elif exc_info and isinstance(exc_info[1], MessageIdInvalidError):
        return
    elif exc_info and isinstance(exc_info[1], OperationalError):
        return
    elif exc_info and isinstance(exc_info[1], ChannelPrivateError):
        return
    elif exc_info and isinstance(exc_info[1], BufferError):
        return
    elif exc_info and isinstance(exc_info[1], RemoteDisconnected):
        return
    elif exc_info and isinstance(exc_info[1], ChatSendMediaForbiddenError):
        return
    elif exc_info and isinstance(exc_info[1], TypeError):
        return
    elif exc_info and isinstance(exc_info[1], URLError):
        return
    elif exc_info and isinstance(exc_info[1], YouBlockedUserError):
        return
    elif exc_info and isinstance(exc_info[1], FloodWaitError):
        return
    elif exc_info and isinstance(exc_info[1], ChunkedEncodingError):
        return
    elif exc_info and isinstance(exc_info[1], TimeoutError):
        return
    elif exc_info and isinstance(exc_info[1], UnicodeEncodeError):
        return
    elif exc_info and isinstance(exc_info[1], ChatWriteForbiddenError):
        return
    elif exc_info and isinstance(exc_info[1], ChatSendStickersForbiddenError):
        return
    elif exc_info and isinstance(exc_info[1], AlreadyInConversationError):
        return
    elif exc_info and isinstance(exc_info[1], ConnectedError):
        return
    elif exc_info and isinstance(exc_info[1], KeyboardInterrupt):
        return
    elif exc_info and isinstance(exc_info[1], OSError):
        return
    elif exc_info and isinstance(exc_info[1], AuthKeyDuplicatedError):
        return
    elif exc_info and isinstance(exc_info[1], ResponseError):
        return
    elif exc_info and isinstance(exc_info[1], SlowModeWaitError):
        return
    elif exc_info and isinstance(exc_info[1], MessageEditTimeExpiredError):
        return
    elif exc_info and isinstance(exc_info[1], PeerIdInvalidError):
        return
    if not python36:
        if exc_info and isinstance(exc_info[1], CancelError):
            return
    if time() <= report_time + 30:
        report_time = time()
        return
    else:
        report_time = time()
        return event


report_time = time()
start_time = datetime.utcnow()
git_hash = run("git rev-parse HEAD", stdout=PIPE, shell=True).stdout.decode()
sentry_sdk.init(
    "https://935d04099b7d4bd889e7ffac488579fc@o416616.ingest.sentry.io/5312335",
    traces_sample_rate=1.0,
    release=git_hash,
    before_send=before_send,
    environment="production",
    integrations=[RedisIntegration()]
)


def redis_status():
    try:
        redis.ping()
        return True
    except BaseException:
        return False


async def log(message):
    logs.info(
        message.replace('`', '\"')
    )
    if not strtobool(config['log']):
        return
    await bot.send_message(
        int(config['log_chatid']),
        message
    )
