import logging

from aiogram.types import Message

from loader import dp
from utils.message import del_msg


@dp.message_handler()
async def unknown(msg: Message):
    logging.info(msg.from_user.id, msg.from_user.username, msg.text)
    await del_msg(msg)
