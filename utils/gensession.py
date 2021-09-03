import os
from sys import executable

try:
    from telethon.errors.rpcerrorlist import ApiIdInvalidError, PhoneNumberInvalidError
    from telethon.sessions import StringSession
    from telethon.sync import TelegramClient
    print("Found an existing installation of Telethon...\nSuccessfully Imported.")
except ImportError:
    print("Installing Telethon...")
    os.system(f"{executable} -m pip install telethon")
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
