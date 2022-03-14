from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
import aiogram.utils.markdown as fmt
from aiogram.utils.exceptions import MessageNotModified

from data.condition import CANCELLATION_STATUS
from keyboards.creating import create_inline_keyboard
from loader import dp
from states.fsm import PreviousMenu, get_fsm_data, get_previous_menu, save_fsm_data
from utils.ozon_express_api.request import cancel_order
from keyboards.inline.admin import get_order_level_3
from keyboards.inline.packer import get_level_8
from utils.message import del_msg
from utils.db import sql
from utils.status import change_status


@dp.message_handler(state=[PreviousMenu.special_cancel])
async def get_msg_for_special_cancel(msg: Message, function: str, tz: str, status, state: FSMContext):
    fsm_data = await get_fsm_data(state, ["posting_number", "menu"])
    await cancel_order(fsm_data["posting_number"], msg.from_user.id, int(402), msg.text)
    await PreviousMenu.back_menu.set()

    msg_id = await sql.get_last_msg(msg.from_user.id)
    if (function == "admin") and (fsm_data["menu"] == "order"):
        await dp.bot.edit_message_text(**await get_order_level_3(function, "manage", msg.from_user.id, tz),
                                       chat_id=msg.from_user.id,
                                       message_id=msg_id)
        await change_status(function, "finish_cancel", status, msg.from_user.id, tz)
    else:
        await dp.bot.edit_message_text(**await get_level_8(function, msg.from_user.id,
                                                           fsm_data["posting_number"], tz, "finish_cancel"),
                                       chat_id=msg.from_user.id, message_id=msg_id)
        await change_status(function, "finish_cancel", status, msg.from_user.id, tz)
    await del_msg(msg)


@dp.callback_query_handler(state=[PreviousMenu.cancel, PreviousMenu.special_cancel])
async def cancel_posting(cll: CallbackQuery, function: str, tz: str, status, state: FSMContext):
    try:
        callback = cll.data.split(":")
        await change_status(function, callback[6], status, cll.from_user.id, tz)
        if callback[2] == '1':
            await PreviousMenu.back_menu.set()
            await cll.message.edit_text(**await get_previous_menu(state), disable_web_page_preview=True)

        elif callback[2] == '2':
            await cll.message.edit_text(**await get_reasons_for_cancel_menu(function, callback[5]))

        elif callback[2] == '3':
            if callback[3] == '402':
                print(callback[5])
                await save_fsm_data(state, posting_number=callback[5])
                await cll.message.edit_text(**await get_another_reasons_for_cancel_menu(function, callback[5]))

            else:
                await PreviousMenu.back_menu.set()
                await cancel_order(callback[5], cll.from_user.id, int(callback[3]))
                fsm_data = await get_fsm_data(state, ["menu"])
                if (function == "admin") and (fsm_data["menu"] == "order"):
                    await cll.message.edit_text(**await get_order_level_3(function, "manage", cll.from_user.id, tz))
                else:
                    await cll.message.edit_text(**await get_level_8(function, cll.from_user.id,
                                                                    callback[5], tz, "finish_cancel"))

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)


async def create_cancel_text(posting_number: str, level: str) -> list:
    text = [fmt.text("Меню отмены\n"),
            fmt.text(fmt.hbold("Отправление:"), fmt.hcode(posting_number))]
    if level == '2':
        text.append(fmt.text("Выберете причину или введите свою, нажав", fmt.hbold("Другая причина")))
    else:
        text.append(fmt.text("Введите причину"))
    return text


async def create_cancel_buttons(posting_number: str, level: str) -> list:
    buttons = []
    if level == '2':
        for key, item in CANCELLATION_STATUS.items():
            action = 'finish_cancel' if key != 402 else 'cancel'
            buttons.append({item.capitalize(): ['cancel', '3', key, '0', posting_number, action]})
        buttons.append({'Назад': ['cancel', '1', '0', '0', posting_number, 'finish_cancel']})
    else:
        buttons.append({'Назад': ['cancel', '2', '0', '0', posting_number, 'back']})
    return buttons


async def get_reasons_for_cancel_menu(function: str, posting_number: str) -> dict:
    await PreviousMenu.cancel.set()
    text = await create_cancel_text(posting_number, '2')
    buttons = await create_cancel_buttons(posting_number, '2')
    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_another_reasons_for_cancel_menu(function: str, posting_number: str):
    await PreviousMenu.special_cancel.set()
    text = await create_cancel_text(posting_number, '3')
    buttons = await create_cancel_buttons(posting_number, '3')
    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}
