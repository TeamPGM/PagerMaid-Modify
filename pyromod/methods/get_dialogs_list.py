from datetime import timedelta

from typing import TYPE_CHECKING

from pagermaid.common.cache import cache

if TYPE_CHECKING:
    from telethon import TelegramClient


@cache(ttl=timedelta(hours=1))
async def get_dialogs_list(client: "TelegramClient"):
    dialogs = []
    async for dialog in client.iter_dialogs():
        dialogs.append(dialog)
    return dialogs
