import asyncio
import base64
import functools
from concurrent.futures import ThreadPoolExecutor
from getpass import getpass
from typing import Optional, TYPE_CHECKING

from pyqrcode import QRCode

from telethon import functions, types
from telethon.errors import BadRequestError, SessionPasswordNeededError

from pagermaid.config import Config
from pyromod.utils.errors import QRCodeWebNeedPWDError, QRCodeWebCodeError

if TYPE_CHECKING:
    from telethon import TelegramClient


async def ainput(
    prompt: str = "",
    *,
    hide: bool = False,
    loop: Optional[asyncio.AbstractEventLoop] = None,
):
    """Just like the built-in input, but async"""
    if isinstance(loop, asyncio.AbstractEventLoop):
        loop = loop
    else:
        loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(1) as executor:
        func = functools.partial(getpass if hide else input, prompt)
        return await loop.run_in_executor(executor, func)


async def sign_in_qrcode(
    client: "TelegramClient",
) -> Optional[str]:
    req = await client(
        functions.auth.ExportLoginTokenRequest(
            api_id=client.api_id,
            api_hash=client.api_hash,
            except_ids=[],
        )
    )

    if isinstance(req, types.auth.LoginToken):
        token = base64.b64encode(req.token)
        return f"tg://login?token={token.decode('utf-8')}"
    elif isinstance(req, types.auth.LoginTokenMigrateTo):
        await client._switch_dc(req.dc_id)
        await client(functions.auth.ImportLoginTokenRequest(token=req.token))
        return await client.get_me()
    elif isinstance(req, types.auth.LoginTokenSuccess):
        user = req.authorization.user
        await client._on_login(user)
        return user


async def authorize_by_qrcode(
    client: "TelegramClient",
):
    while True:
        qrcode = None
        try:
            qrcode = await sign_in_qrcode(client)
        except BadRequestError as e:
            print(e.message)
        except SessionPasswordNeededError as e:
            print(e.message)
            while True:
                password = await ainput("Enter password: ")

                try:
                    await client.sign_in(password=password)
                except BadRequestError as e:
                    print(e.message)
        if isinstance(qrcode, str):
            qr_obj = QRCode(qrcode)
            try:
                qr_obj.png("data/qrcode.png", scale=6)
            except Exception:
                print("Save qrcode.png failed.")
            print(qr_obj.terminal())
            print(
                f"Scan the QR code above, the qrcode.png file or visit {qrcode} to log in.\n"
            )
            print(
                "QR code will expire in 20 seconds. If you have scanned it, please wait..."
            )
            await asyncio.sleep(20)
        elif qrcode is not None:
            return qrcode


async def authorize_by_qrcode_web(
    client: "TelegramClient",
    password: Optional[str] = None,
):
    qrcode = None
    try:
        if password:
            raise SessionPasswordNeededError("")
        qrcode = await sign_in_qrcode(client)
    except BadRequestError as e:
        raise e
    except SessionPasswordNeededError as e:
        try:
            if password:
                return await client.sign_in(password=password)
        except BadRequestError as e:
            raise e
        raise QRCodeWebNeedPWDError("") from e
    if isinstance(qrcode, str):
        raise QRCodeWebCodeError(qrcode)
    elif qrcode is not None:
        return qrcode


async def start_client(client: "TelegramClient"):
    if not client.is_connected():
        await client.connect()
    is_authorized = await client.is_user_authorized()

    try:
        if not is_authorized and Config.QRCODE_LOGIN:
            await authorize_by_qrcode(client)
        await client.start()
    except (Exception, KeyboardInterrupt):
        await client.disconnect()
        raise
