from aiogram.types import Message
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.handler import SkipHandler

from loader import dp
from data.condition import FUNCTION
from utils.message import del_msg, update_msg
from keyboards.inline import change_func


@dp.message_handler(CommandStart())
async def start_courier(msg: Message, function, status):
    if function in FUNCTION:
        func = await change_func(function)
        new_msg = await msg.answer(**await func.get_level_1(function, status))

        await update_msg(new_msg)
        await del_msg(msg)

    else:
        raise SkipHandler
