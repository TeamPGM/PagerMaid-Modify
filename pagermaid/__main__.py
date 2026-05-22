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
RETRYABLE_CONNECTION_ERRORS = (
    OSError,
    ConnectionError,
    TimeoutError,
    asyncio.TimeoutError,
)


class ShutdownController:
    def __init__(self):
        self.requested = False
        self.current_task = None

    def request(self):
        self.requested = True
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()

    async def wait(self, awaitable):
        if self.requested:
            if asyncio.iscoroutine(awaitable):
                awaitable.close()
            return False, None
        task = asyncio.ensure_future(awaitable)
        self.current_task = task
        try:
            result = await task
            return not self.requested, result
        except asyncio.CancelledError:
            if self.requested:
                return False, None
            raise
        finally:
            if self.current_task is task:
                self.current_task = None


async def sleep_before_retry(delay, shutdown):
    logs.warning(f"{lang('telegram_retrying')} {delay}s")
    keep_running, _ = await shutdown.wait(asyncio.sleep(delay))
    if not keep_running:
        return False, delay
    return True, min(delay * 2, MAX_RETRY_DELAY)


async def idle(shutdown):
    retry_delay = INITIAL_RETRY_DELAY

    async def wait_before_retry():
        nonlocal retry_delay
        keep_running, retry_delay = await sleep_before_retry(retry_delay, shutdown)
        return keep_running

    def signal_handler(_, __):
        shutdown.request()
        if web.web_server_task:
            web.web_server_task.cancel()

    for s in (SIGINT, SIGTERM, SIGABRT):
        signal_fn(s, signal_handler)

    try:
        while True:
            if shutdown.requested:
                break

            if Config.WEB_ENABLE and Config.WEB_LOGIN:
                keep_running, _ = await shutdown.wait(asyncio.sleep(600))
                if not keep_running:
                    break
                continue

            if not bot.is_connected():
                try:
                    logs.info(lang("telegram_connecting"))
                    keep_running, _ = await shutdown.wait(bot.connect())
                    if not keep_running:
                        break
                except RETRYABLE_CONNECTION_ERRORS as e:
                    logs.warning(f"{lang('telegram_connection_failed')}: {type(e).__name__}: {e}")
                    if not await wait_before_retry():
                        break
                    continue

            started_at = asyncio.get_running_loop().time()
            disconnected_logged = False
            try:
                keep_running, _ = await shutdown.wait(bot._run_until_disconnected())
                if not keep_running:
                    break
            except RETRYABLE_CONNECTION_ERRORS as e:
                logs.warning(f"{lang('telegram_disconnected')}: {type(e).__name__}: {e}")
                disconnected_logged = True

            if getattr(bot, "_should_restart", False):
                break

            if asyncio.get_running_loop().time() - started_at >= STABLE_RETRY_RESET_AFTER:
                retry_delay = INITIAL_RETRY_DELAY

            if not disconnected_logged:
                logs.warning(lang("telegram_disconnected"))
            if not await wait_before_retry():
                break
    except asyncio.CancelledError:
        if shutdown.requested:
            return
        raise


async def console_bot():
    try:
        logs.info(lang("telegram_connecting"))
        await start_client(bot)
        me = await bot.get_me()
    except AuthKeyError:
        logs.error(lang("telegram_auth_key_invalid"))
        SessionFileManager.safe_remove_session()
        exit()
    except RETRYABLE_CONNECTION_ERRORS as e:
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
    shutdown = ShutdownController()
    web.set_stop_handler(shutdown.request)
    if not scheduler.running:
        scheduler.start()
    await web.start()
    try:
        if not (Config.WEB_ENABLE and Config.WEB_LOGIN):
            retry_delay = INITIAL_RETRY_DELAY
            while True:
                try:
                    keep_running, _ = await shutdown.wait(console_bot())
                    if not keep_running:
                        return
                    break
                except RETRYABLE_CONNECTION_ERRORS:
                    keep_running, retry_delay = await sleep_before_retry(
                        retry_delay, shutdown
                    )
                    if not keep_running:
                        return
            logs.info(lang("start"))
        else:
            keep_running, _ = await shutdown.wait(web_bot())
            if not keep_running:
                return
        await idle(shutdown)
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
