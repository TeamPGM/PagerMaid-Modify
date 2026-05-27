import shutil
import subprocess
import sys
from sys import executable


def install_package(package: str):
    if shutil.which("uv"):
        command = ["uv", "pip", "install", "--python", executable, package]
    else:
        command = [executable, "-m", "pip", "install", package]
    try:
        subprocess.check_call(command)  # nosec B603 - command is built from a controlled allow-list
    except subprocess.CalledProcessError as exc:
        print(f"Failed to install {package}: {exc}")
        sys.exit(exc.returncode or 1)

try:
    from telethon.errors.rpcerrorlist import ApiIdInvalidError, PhoneNumberInvalidError
    from telethon.sessions import StringSession
    from telethon.sync import TelegramClient

    print("Found an existing installation of Telethon...\nSuccessfully Imported.")
except ImportError:
    print("Installing Telethon...")
    install_package("telethon")
    print("Done. Installed and imported Telethon.")
    from telethon.errors.rpcerrorlist import ApiIdInvalidError, PhoneNumberInvalidError
    from telethon.sessions import StringSession
    from telethon.sync import TelegramClient

API_ID = 0
try:
    API_ID = int(input("Please enter your API ID: "))
except ValueError:
    print("APP ID must be an integer.\nQuitting...")
    exit(0)
except Exception as e:
    raise e

API_HASH = input("Please enter your API HASH: ")
try:
    with TelegramClient(StringSession(), API_ID, API_HASH) as bot:
        print("Generating a user session...")
        bot.send_message(
            "me",
            f"**PagerMaid** `String SESSION`:\n\n`{bot.session.save()}`",
        )
        print("Your SESSION has been generated. Check your telegram saved messages!")
        exit(0)
except ApiIdInvalidError:
    print("Your API ID/API HASH combination is invalid. Kindly recheck.\nQuitting...")
    exit(0)
except ValueError:
    print("API HASH must not be empty!\nQuitting...")
    exit(0)
except PhoneNumberInvalidError:
    print("The phone number is invalid!\nQuitting...")
    exit(0)
