from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter, CommandStart
from aiogram.types import Message, ChatType
from aiogram.utils.exceptions import MessageNotModified
#
from loader import dp
from utils.db_api import extra
#
#
# @dp.message_handler(CommandStart(), ChatTypeFilter(chat_type=ChatType.PRIVATE))
# async def start_unknown(msg: Message, state: FSMContext):
#     await msg_info_log(msg)
#     await extra.check_state(state)
#     await extra.protection(msg)
#     await extra.del_msg(msg)
#
#
@dp.message_handler()
async def unknown(msg: Message):
    print(msg)
    await extra.del_msg(msg)
#
#
# @dp.errors_handler(exception=MessageNotModified)
# async def message_not_modified_handler(update, error):
#     return True
