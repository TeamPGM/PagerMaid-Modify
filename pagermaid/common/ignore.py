from telethon.tl.types import Channel, Chat

from pagermaid.services import bot
from pagermaid.utils import Sub

ignore_groups_manager = Sub("ignore_groups")


def to_dict(entity):
    """Convert entity to a dictionary."""
    if not entity:
        return {}
    return {
        "id": entity.id,
        "title": entity.title,
        "type": type(entity).__name__,
    }


async def get_group_list():
    try:
        return [
            to_dict(dialog.entity)
            for dialog in await bot.get_dialogs_list()
            if (
                dialog.entity
                and (
                    (type(dialog.entity) is Channel and not dialog.entity.broadcast)
                    or type(dialog.entity) is Chat
                )
            )
        ]
    except BaseException:
        return []
