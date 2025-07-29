import telethon
from telethon.tl.patched import Message

from pagermaid.dependence import add_delete_message_job
from ..methods.get_dialogs_list import get_dialogs_list as get_dialogs_list_func

from ..utils import patch, patchable
from ..utils.handler_priority import HandlerList


@patch(telethon.TelegramClient)
class TelegramClient(telethon.TelegramClient):
    @patchable
    def __init__(self, *args, **kwargs):
        self.old__init__(*args, **kwargs)
        self._event_builders = HandlerList()

    @patchable
    async def get_dialogs_list(self: "telethon.TelegramClient"):
        return await get_dialogs_list_func(self)


# pagermaid-modify


@patch(telethon.tl.patched.Message)
class Message(telethon.tl.patched.Message):
    @patchable
    async def safe_delete(self, *args, **kwargs):
        try:
            return await self.delete(*args, **kwargs)
        except Exception:  # noqa
            return False

    @patchable
    async def delay_delete(self, delay: int = 60):
        add_delete_message_job(self, delay)
