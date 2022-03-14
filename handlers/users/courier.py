from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.exceptions import MessageNotModified

from loader import dp
from states.fsm import PreviousMenu, get_fsm_data, save_fsm_data
from data.condition import CALLBACK
from keyboards.inline import courier
from utils.message import del_msg, update_msg, push_info_msg
from utils.geo import create_keyboard_to_check_location
from utils.status import change_status


@dp.callback_query_handler(CALLBACK['courier'].filter(menu='delivery'), state='*')
async def open_bot_menu(cll: CallbackQuery, callback_data: dict, function: str, tz: str, status, state: FSMContext):
    """
    Menu: Order
    """
    try:
        await change_status(function, callback_data['action'], status, cll.from_user.id, tz)
        if callback_data['level'] == '2':
            await cll.message.edit_text(**await courier.get_level_2(function, cll))

        elif callback_data['level'] == '3':
            await cll.message.edit_text(**await courier.get_level_3(function, cll))

        elif callback_data['level'] == '4':
            if callback_data['action'] == 'open':
                await save_fsm_data(state, text=cll.message.html_text, reply_markup=cll.message.reply_markup)
                await cll.message.edit_text(**await courier.get_level_4(function, cll),
                                            disable_web_page_preview=True)

            elif callback_data['action'] == 'back':
                await cll.message.edit_text(**await get_fsm_data(state, ["text", "reply_markup"]))

        elif callback_data['level'] == '5':
            if callback_data['action'] == 'added':
                await push_info_msg(cll, 'Этот заказ является обязательным, т.к. ближайший по сроку исполнения')

            else:
                await cll.message.edit_reply_markup(**await courier.get_level_5(cll))

        elif callback_data['level'] == '6':
            await cll.message.edit_text(**await courier.get_level_6(function, cll, state, tz))

        elif callback_data['level'] == '7':
            if callback_data['action'] == 'open':
                await save_fsm_data(state, text=cll.message.html_text, reply_markup=cll.message.reply_markup)
                await cll.message.edit_text(**await courier.get_level_7(function, cll, state),
                                            disable_web_page_preview=True)

            elif callback_data['action'] == 'back':
                await cll.message.edit_text(**await get_fsm_data(state, ["text", "reply_markup"]))

        elif callback_data['level'] == '8':
            if callback_data['action'] == 'open':
                await cll.message.edit_text(**await courier.get_level_8(function, cll, state))

        elif callback_data['level'] == '9':
            if callback_data['action'] in ['delivered', 'return', 'no_call']:
                await PreviousMenu.geo.set()
                await save_fsm_data(state, text=cll.message.html_text,
                                    reply_markup=cll.message.reply_markup, action=cll.data)

                new_msg = await cll.message.answer(**await create_keyboard_to_check_location())
                await update_msg(new_msg)
                await del_msg(cll.message)

            else:
                await cll.message.edit_text(**await courier.get_level_9(function, tz, cll))

        elif callback_data['level'] == '10':
            await cll.message.edit_text(**await courier.get_level_10(function, cll))

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)
