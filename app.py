import asyncio
import logging

from loader import dp, bot
import middlewares, filters, handlers
from utils.db.database import start_sql_bd
from utils.message import send_message_to_logs
from polling import start_polling_api


async def main():
    await start_sql_bd()

    await start_polling_api()
    await send_message_to_logs(start_up=True)

    try:
        await dp.skip_updates()
        await dp.start_polling()

    finally:
        await send_message_to_logs(turn_off=True)

        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())

    except (KeyboardInterrupt, SystemExit):
        logging.error("Бот остановлен!")
