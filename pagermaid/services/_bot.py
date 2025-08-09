import python_socks
import pyromod.listen

from telethon import TelegramClient
from telethon.sessions import StringSession

from pagermaid.config import Config
from pagermaid.utils import SessionFileManager
from pagermaid.version import pgm_version

client_proxy = None
if Config.PROXY_ADDRESS and Config.PROXY_PORT:
    client_proxy = (
        python_socks.ProxyType.SOCKS5,
        Config.PROXY_ADDRESS,
        int(Config.PROXY_PORT),
    )
elif Config.PROXY_HTTP_ADDRESS and Config.PROXY_HTTP_PORT:
    client_proxy = (
        python_socks.ProxyType.HTTP,
        Config.PROXY_HTTP_ADDRESS,
        int(Config.PROXY_HTTP_PORT),
    )
session = SessionFileManager.get_session_file_path()
if Config.STRING_SESSION:
    session = StringSession(Config.STRING_SESSION)

bot = TelegramClient(
    session,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    use_ipv6=Config.IPV6,
    proxy=client_proxy,
    app_version=f"PGM {pgm_version}",
)
