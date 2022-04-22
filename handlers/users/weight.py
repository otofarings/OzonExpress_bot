from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
import aiogram.utils.markdown as fmt
from aiogram.utils.exceptions import MessageNotModified

from loader import dp
from utils.db import sql
from states.fsm import PreviousMenu, get_fsm_data, get_previous_menu
from utils.message import del_msg
from utils.formate_text import weighting_product, txt
from utils.status import change_status
from keyboards.creating import create_reply_markup
from keyboards.inline.packer import get_level_5


@dp.message_handler(state=[PreviousMenu.weight])
async def get_msg_with_weight(msg: Message, function: str, tz: str, status, state: FSMContext):
    try:
        correct = False
        msg_id = await sql.get_last_msg(msg.from_user.id)
        fsm_data = await get_fsm_data(state, ["posting_number", "sku", "order_description"])

        if msg.text.isdigit():
            if (10 < int(msg.text) < 10000) or (int(msg.text) == 0):
                await sql.update_product_weight(int(fsm_data["sku"]), int(msg.text), fsm_data["posting_number"])
                await PreviousMenu.back_menu.set()

                await dp.bot.edit_message_text(**await get_level_5(function, state, args=[fsm_data["posting_number"],
                                                                                          fsm_data["sku"],
                                                                                          "finish_weight"]),
                                               text=fsm_data["order_description"],
                                               chat_id=msg.from_user.id,
                                               message_id=msg_id,
                                               disable_web_page_preview=True)
                await change_status(function, "finish_weight", status, msg.from_user.id, tz)
                correct = True

        if not correct:
            await dp.bot.edit_message_text(**await get_weight_menu(function, fsm_data["sku"],
                                                                   fsm_data["posting_number"], True),
                                           chat_id=msg.from_user.id,
                                           message_id=msg_id,
                                           disable_web_page_preview=True)

    except MessageNotModified:
        return True

    finally:
        await del_msg(msg)


@dp.callback_query_handler(state=[PreviousMenu.weight])
async def weight_product(cll: CallbackQuery, function: str, tz: str, status, state: FSMContext):
    try:
        callback = cll.data.split(":")
        await change_status(function, callback[6], status, cll.from_user.id, tz)
        if callback[2] == '1':
            await PreviousMenu.back_menu.set()
            await cll.message.edit_text(**await get_previous_menu(state),
                                        disable_web_page_preview=True)

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)


async def create_weight_text(sku: str, posting_number: str, not_digit: bool = False) -> list:
    name = await sql.get_product_name(posting_number, int(sku))
    return await weighting_product(str(name), not_digit)


async def create_weight_buttons() -> list:
    buttons = [{'Назад': ['weight', '1', '0', '0', '0', 'finish_weight']}]
    return buttons


async def get_weight_menu(function: str, sku: str, posting_number: str, not_digit: bool = False) -> dict:
    await PreviousMenu.weight.set()
    text = await create_weight_text(sku, posting_number, not_digit)
    buttons = await create_weight_buttons()
    return await create_reply_markup(await txt(text), function, buttons)
