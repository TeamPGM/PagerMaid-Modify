import asyncio
from os import sep
from pathlib import Path
from signal import signal as signal_fn, SIGINT, SIGTERM, SIGABRT
from sys import path, platform, exit

from telethon.errors.rpcerrorlist import AuthKeyError

from pagermaid.common.reload import load_all
from pagermaid.config import Config
from pagermaid.dependence import scheduler
from pagermaid.services import bot
from pagermaid.static import working_dir
from pagermaid.utils import lang, logs, SessionFileManager
from pagermaid.web import web
from pagermaid.web.api.web_login import web_login
from pyromod.methods.sign_in_qrcode import start_client

bot.PARENT_DIR = Path(working_dir)
path.insert(1, f"{working_dir}{sep}plugins")

INITIAL_RETRY_DELAY = 5
MAX_RETRY_DELAY = 120
STABLE_RETRY_RESET_AFTER = 300


async def sleep_before_retry(delay):
    logs.warning(f"{lang('telegram_retrying')} {delay}s")
    await asyncio.sleep(delay)
    return min(delay * 2, MAX_RETRY_DELAY)


async def idle():
    task = None
    idle_task = asyncio.current_task()
    retry_delay = INITIAL_RETRY_DELAY

    def signal_handler(_, __):
        if web.web_server_task:
            web.web_server_task.cancel()
        if task and not task.done():
            task.cancel()
        elif idle_task and not idle_task.done():
            idle_task.cancel()

    for s in (SIGINT, SIGTERM, SIGABRT):
        signal_fn(s, signal_handler)

    try:
        while True:
            if Config.WEB_ENABLE and Config.WEB_LOGIN:
                t = asyncio.sleep(600)
                task = asyncio.create_task(t)
                web.bot_main_task = task
                try:
                    await task
                except asyncio.CancelledError:
                    break
                continue

            if not bot.is_connected():
                try:
                    logs.info(lang("telegram_connecting"))
                    await bot.connect()
                except (OSError, ConnectionError, TimeoutError, asyncio.TimeoutError) as e:
                    logs.warning(f"{lang('telegram_connection_failed')}: {type(e).__name__}: {e}")
                    retry_delay = await sleep_before_retry(retry_delay)
                    continue

            started_at = asyncio.get_running_loop().time()
            t = bot._run_until_disconnected()
            task = asyncio.create_task(t)
            web.bot_main_task = task
            try:
                await task
            except asyncio.CancelledError:
                break
            except Exception as e:
                logs.warning(f"{lang('telegram_disconnected')}: {type(e).__name__}: {e}")

            if getattr(bot, "_should_restart", False):
                break

            if asyncio.get_running_loop().time() - started_at >= STABLE_RETRY_RESET_AFTER:
                retry_delay = INITIAL_RETRY_DELAY

            logs.warning(lang("telegram_disconnected"))
            retry_delay = await sleep_before_retry(retry_delay)
    except asyncio.CancelledError:
        if task and not task.done():
            task.cancel()


async def console_bot():
    try:
        logs.info(lang("telegram_connecting"))
        await start_client(bot)
        me = await bot.get_me()
    except AuthKeyError:
        logs.error(lang("telegram_auth_key_invalid"))
        SessionFileManager.safe_remove_session()
        exit()
    except (OSError, ConnectionError, TimeoutError, asyncio.TimeoutError) as e:
        logs.warning(f"{lang('telegram_connection_failed')}: {type(e).__name__}: {e}")
        raise
    bot.me = me
    if me.bot:
        SessionFileManager.safe_remove_session()
        exit()
    logs.info(f"{lang('save_id')} {me.first_name}({me.id})")
    await load_all()


async def web_bot():
    try:
        await web_login.init()
    except AuthKeyError:
        SessionFileManager.safe_remove_session()
        exit()
    if bot.me is not None:
        me = await bot.get_me()
        if me.bot:
            SessionFileManager.safe_remove_session()
            exit()
    else:
        logs.info("Please use web to login, path: web_login .")


async def main():
    logs.info(lang("platform") + platform + lang("platform_load"))
    if not scheduler.running:
        scheduler.start()
    await web.start()
    if not (Config.WEB_ENABLE and Config.WEB_LOGIN):
        retry_delay = INITIAL_RETRY_DELAY
        while True:
            try:
                await console_bot()
                break
            except (OSError, ConnectionError, TimeoutError, asyncio.TimeoutError):
                retry_delay = await sleep_before_retry(retry_delay)
        logs.info(lang("start"))
    else:
        await web_bot()
    try:
        await idle()
    finally:
        if scheduler.running:
            scheduler.shutdown()
        try:
            await bot.disconnect()
        except ConnectionError:
            pass
        if web.web_server:
            try:
                await web.web_server.shutdown()
            except AttributeError:
                pass


bot.loop.run_until_complete(main())
