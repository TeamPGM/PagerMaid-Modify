""" PagerMaid initialization. """

from subprocess import run, PIPE
from datetime import datetime
from time import time
from os import getcwd, makedirs, environ
from os.path import exists
from sys import version_info, platform
from yaml import load, FullLoader
from json import load as load_json
from shutil import copyfile
from redis import StrictRedis
from logging import getLogger, INFO, DEBUG, ERROR, StreamHandler, basicConfig
from distutils.util import strtobool
from coloredlogs import ColoredFormatter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telethon import TelegramClient
from telethon.sessions import StringSession

from languages.languages import Lang

persistent_vars = {}
module_dir = __path__[0]
working_dir = getcwd()
config = None
help_messages = {}
scheduler = AsyncIOScheduler()
if not scheduler.running:
    scheduler.configure(timezone="Asia/ShangHai")
    scheduler.start()
version = 0.1
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
language = Lang(config["application_language"])

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
    return language.get(text)


analytics = None
try:
    allow_analytics = strtobool(config.get('allow_analytic', 'True'))
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
proxy_addr = config.get('proxy_addr', '').strip()
proxy_port = config.get('proxy_port', '').strip()
http_addr = config.get('http_addr', '').strip()
http_port = config.get('http_port', '').strip()
mtp_addr = config.get('mtp_addr', '').strip()
mtp_port = config.get('mtp_port', '').strip()
mtp_secret = config.get('mtp_secret', '').strip()
redis_host = config.get('redis').get('host', 'localhost')
redis_port = config.get('redis').get('port', 6379)
redis_db = config.get('redis').get('db', 14)
redis_password = config.get('redis').get('password', '')
use_ipv6 = bool(strtobool(config.get('ipv6', 'False')))
silent = bool(strtobool(config.get('silent', 'True')))
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
user_bot = False
redis = StrictRedis(host=redis_host, port=redis_port, db=redis_db, password=redis_password)


async def save_id():
    global user_id, user_bot
    me = await bot.get_me()
    user_id = me.id
    user_bot = me.bot
    if me.username is not None:
        if allow_analytics:
            analytics.identify(user_id, {
                'name': me.first_name,
                'username': me.username,
                'bot': f"{user_bot}"
            })
    else:
        if allow_analytics:
            analytics.identify(user_id, {
                'name': me.first_name,
                'bot': f"{user_bot}"
            })
    if user_bot:
        user_bot = me.username
    logs.info(f"{lang('save_id')} {me.first_name}({user_id})")


with bot:
    bot.loop.run_until_complete(save_id())

report_time = time()
start_time = datetime.utcnow()
git_hash = run("git rev-parse HEAD", stdout=PIPE, shell=True).stdout.decode()


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
    try:
        await bot.send_message(
            int(config['log_chatid']),
            message
        )
    except ValueError:
        pass
