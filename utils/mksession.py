from telethon import TelegramClient
from yaml import load, FullLoader

config = load(open(r"config.yml"), Loader=FullLoader)
api_key = config['api_key']
api_hash = config['api_hash']

bot = TelegramClient('pagermaid', api_key, api_hash)
bot.start()
