from typing import List, Optional, TYPE_CHECKING
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from telethon import TelegramClient as OldClient
from telethon.tl.patched import Message as OldMessage

if TYPE_CHECKING:
    from telethon.types import User
    from telethon.tl.custom import Dialog


class Message(OldMessage):
    arguments: str
    parameter: List

    async def delay_delete(self, delay: int = 60) -> Optional[bool]:
        """Deletes the message after a specified amount of seconds."""

    async def safe_delete(self) -> None:
        """Safely deletes the message."""


class Client(OldClient):
    me: Optional["User"] = None
    job: Optional[AsyncIOScheduler] = None

    async def get_dialogs_list(self) -> List["Dialog"]:
        """Get a list of all dialogs."""
