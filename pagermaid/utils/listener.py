from typing import TYPE_CHECKING

from telethon.errors import RPCError

from pagermaid.dependence import status_sudo, get_sudo_list
from pagermaid.group_manager import enforce_permission

if TYPE_CHECKING:
    from pagermaid.enums import Message


def get_permission_name(is_plugin: bool, need_admin: bool, command: str) -> str:
    """Get permission name."""
    if is_plugin:
        return f"plugins_root.{command}" if need_admin else f"plugins.{command}"
    else:
        return f"system.{command}" if need_admin else f"modules.{command}"


def sudo_filter(permission: str, handler):
    async def if_sudo(message: "Message"):
        if not status_sudo():
            return False
        try:
            from_id = message.sender_id
            sudo_list = get_sudo_list()
            if from_id not in sudo_list:
                if message.chat_id in sudo_list:
                    return enforce_permission(message.chat.id, permission)
                return False
            return enforce_permission(from_id, permission)
        except Exception:  # noqa
            return False

    async def handler2(context: "Message"):
        if not await if_sudo(context):
            return
        return await handler(context)

    return handler2


def from_self(message: "Message") -> bool:
    if message.out:
        return True
    return message.sender and message.sender.is_self


def from_msg_get_sudo_uid(message: "Message") -> int:
    """Get the sudo uid from the message."""
    from_id = message.sender_id
    return from_id if from_id in get_sudo_list() else message.chat_id


def check_manage_subs(message: "Message") -> bool:
    return from_self(message) or enforce_permission(
        from_msg_get_sudo_uid(message), "modules.manage_subs"
    )


def format_exc(e: BaseException) -> str:
    if isinstance(e, RPCError):
        return f"<code>API {str(e)}</code>"
    return f"<code>{e.__class__.__name__}: {e}</code>"
