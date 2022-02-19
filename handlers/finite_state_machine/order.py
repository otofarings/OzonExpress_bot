from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from loader import dp
from states.fsm import CancelReason
from keyboards.inline import admin
from utils.db_api import extra


async def start_another_cancel_order_reason(chat_id: int, callback: dict, state):
    await CancelReason.reason.set()
    msg_id = await extra.get_last_msg(chat_id)
    async with state.proxy() as data:
        data['order_id'] = callback['item_id']
        data['chat_id'], data['msg_id'] = chat_id, msg_id
    await dp.bot.edit_message_text(text=f'Отмена заказа\nВведите причину',
                                   reply_markup=await admin.get_order_cancel_back_menu(callback),
                                   chat_id=chat_id,
                                   message_id=msg_id)


@dp.message_handler(state=CancelReason.reason)
async def finish_update_api_key(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        callback = data
    # await extra.update_api_key(msg.text, int(callback['seller']))
    # await dp.bot.edit_message_text(**await creator.get_api_seller_menu(callback),
    #                                chat_id=msg.chat.id,
    #                                message_id=int(callback['msg_id']))
    await state.finish()
    await extra.del_msg(msg)
