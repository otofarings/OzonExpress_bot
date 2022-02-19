import logging

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from data import config


logging.basicConfig(level=logging.INFO, format=config.LOGGING_FORMAT)

storage = MemoryStorage()
bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)

dp = Dispatcher(bot, storage=storage)
