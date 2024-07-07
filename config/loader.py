from aiogram import Bot, Dispatcher

from config.config import TOKEN

# from aiogram.client.bot import DefaultBotProperties


ENGINE = 'sqlite+aiosqlite:///db.sqlite3'
ECHO = True

# default_properties = DefaultBotProperties(parse_mode='HTML')

bot = Bot(token=TOKEN)
dp = Dispatcher()
