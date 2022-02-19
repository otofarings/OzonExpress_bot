from aiogram import Dispatcher

from loader import config
from utils.db_api.database import db_query
from .proccess_time import get_time


async def send_message_to_logs(dp: Dispatcher, start_up: bool = False, turn_off: bool = False, txt=''):
    for recipient in [config.MODER_LOGS]:
        if start_up:
            txt = f"Бот Запущен!"
            await db_query(func='execute',
                           sql="""INSERT INTO logs_bot_running (start_date) VALUES($1);""",
                           kwargs=[await get_time()])
        elif turn_off:
            txt = f"Бот Остановлен!"
            await db_query(func='execute',
                           sql="""UPDATE logs_bot_running SET finish_date = $1 
                                          WHERE id = (SELECT max(id) FROM logs_bot_running);""",
                           kwargs=[await get_time()])
        await dp.bot.send_message(recipient, f'{await get_time()}: {txt}')
