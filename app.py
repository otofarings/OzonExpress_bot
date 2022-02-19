import asyncio
import logging

from loader import dp, bot
import middlewares, filters, handlers
from utils.db_api.tables import create_tables
from utils.notifications import send_message_to_logs
from utils.db_api.database import db_query
from data.config import DEBUG
from polling import start_polling

logger = logging.getLogger(__name__)


async def main():
    await db_query(dir_func=create_tables)
    # await send_message_to_logs(dp, start_up=True)
    if not DEBUG:
        await start_polling()
    try:
        await dp.skip_updates()
        await dp.start_polling()
    finally:
        # await send_message_to_logs(dp, turn_off=True)
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Бот остановлен!")
