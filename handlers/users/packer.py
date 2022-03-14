from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.exceptions import MessageNotModified

from loader import dp
from states.fsm import get_fsm_data, save_fsm_data
from data.condition import CALLBACK
from . cancel_posting import get_reasons_for_cancel_menu
from .weight import get_weight_menu
from keyboards.inline import packer
from utils.status import change_status


@dp.callback_query_handler(CALLBACK['packer'].filter(menu='package'), state='*')
async def open_packer_menu(cll: CallbackQuery, callback_data: dict, function: str, tz: str, status, state: FSMContext):
    """
    Menu: Order
    """
    try:
        await change_status(function, callback_data['action'], status, cll.from_user.id, tz)
        if callback_data['level'] == '2':
            await cll.message.edit_text(**await packer.get_level_2(function, cll))

        elif callback_data['level'] == '3':
            await cll.message.edit_text(**await packer.get_level_3(function, cll, state), disable_web_page_preview=True)

        elif callback_data['level'] == '4':
            await cll.message.edit_text(**await packer.get_level_4(function, cll, state), disable_web_page_preview=True)

        elif callback_data['level'] == '5':
            if callback_data['action'] == "start_packaging":
                await save_fsm_data(state, order_description=cll.message.html_text)
                await packer.start_package(cll, tz)

            await cll.message.edit_text(**await packer.get_level_5(function, cll),
                                        text=(await get_fsm_data(state, ["order_description"]))["order_description"],
                                        disable_web_page_preview=True)

        elif callback_data['level'] == '6':
            await save_fsm_data(state, text=cll.message.html_text)
            await cll.message.edit_text(**await packer.get_level_6(function, cll))

        elif callback_data['level'] == '7':
            if callback_data['action'] == 'open':
                await save_fsm_data(state, text=cll.message.html_text, reply_markup=cll.message.reply_markup)
                await cll.message.edit_text(**await packer.get_level_7(function, cll))

            elif callback_data['action'] in ['roll_up', 'roll_down']:
                await cll.message.edit_text(**await packer.get_level_7(function, cll))

            elif callback_data['action'] == 'back':
                await cll.message.edit_text(**await get_fsm_data(state, ['text', 'reply_markup']),
                                            disable_web_page_preview=True)

        elif callback_data['level'] == '8':
            await cll.message.edit_text(**await packer.get_level_8(function, cll.from_user.id,
                                                                   callback_data["item_id"], tz,
                                                                   callback_data["action"]))

        elif callback_data['level'] == '9':
            if callback_data['action'] == 'start_cancel':
                await save_fsm_data(state, text=cll.message.html_text, reply_markup=cll.message.reply_markup,
                                    menu=callback_data["menu"])
                await cll.message.edit_text(**await get_reasons_for_cancel_menu(function, callback_data["item_id"]))

            elif callback_data['action'] == 'start_weight':
                await save_fsm_data(state, text=cll.message.html_text, reply_markup=cll.message.reply_markup,
                                    posting_number=callback_data["item_id"], sku=callback_data["option"])
                await cll.message.edit_text(**await get_weight_menu(function,
                                                                    callback_data["option"], callback_data["item_id"]))

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)
