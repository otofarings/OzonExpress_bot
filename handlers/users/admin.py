from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.exceptions import MessageNotModified

from data.condition import CALLBACK
from handlers.finite_state_machine.employee import start_create_new_user
from . cancel_posting import get_reasons_for_cancel_menu
from loader import dp
from keyboards.inline import admin, courier, packer
from states.fsm import PreviousMenu, get_fsm_data, save_fsm_data
from utils.message import del_msg, update_msg, push_info_msg
from utils.geo import create_keyboard_to_check_location
from utils.status import change_status
from .weight import get_weight_menu


@dp.callback_query_handler(CALLBACK['admin'].filter(menu='order'), state='*')
async def open_order_menu(cll: CallbackQuery, callback_data: dict, function: str, tz: str, status, state: FSMContext):
    try:
        await change_status(function, callback_data['action'], status, cll.from_user.id, tz)
        if callback_data['level'] == '2':
            await cll.message.edit_text(**await admin.get_order_level_2(function))

        elif callback_data['level'] == '3':
            await cll.message.edit_text(**await admin.get_order_level_3(function, callback_data['option'],
                                                                        cll.from_user.id, tz))

        elif callback_data['level'] == '4':
            if callback_data['action'] == 'assign':
                pass

            await cll.message.edit_text(**await admin.get_order_level_4(function, cll),
                                        disable_web_page_preview=True)

        elif callback_data['level'] == '5':
            if callback_data['action'] == 'start_cancel':
                await save_fsm_data(state, text=cll.message.html_text, reply_markup=cll.message.reply_markup,
                                    menu=callback_data["menu"])
                await cll.message.edit_text(**await get_reasons_for_cancel_menu(function, callback_data["item_id"]))

        elif callback_data['level'] == '6':
            if callback_data['action'] == 'open':
                await cll.message.edit_text(**await admin.get_user_for_reassign_menu(cll, state))

            else:
                await cll.message.edit_text(**await admin.get_user_for_reassign_menu(state=state))

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)


@dp.callback_query_handler(CALLBACK['admin'].filter(menu='user'), state='*')
async def open_user_menu(cll: CallbackQuery, callback_data: dict, function: str, state: FSMContext):
    try:
        if callback_data['level'] == '2':
            await cll.message.edit_text(**await admin.get_employee_level_2(function))

        elif callback_data['level'] == '3':
            if callback_data['action'] == 'delete':
                await push_info_msg(cll, "Сотрудник был успешно удален")

            await cll.message.edit_text(**await admin.get_employee_level_3(function, cll))

        elif callback_data['level'] == '4':
            if callback_data['action'] == 'add':
                await start_create_new_user(chat_id=cll.from_user.id, callback=callback_data, state=state)

            else:
                await cll.message.edit_text(**await admin.get_employee_level_4(function, cll))

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)


@dp.callback_query_handler(CALLBACK['admin'].filter(menu='delivery'), state='*')
async def open_courier_menu(cll: CallbackQuery, callback_data: dict, function: str, tz: str, status, state: FSMContext):
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


@dp.callback_query_handler(CALLBACK['admin'].filter(menu='package'), state='*')
async def open_packer_menu(cll: CallbackQuery, callback_data: dict, function: str, tz: str, status, state: FSMContext):
    try:
        await change_status(function, callback_data['action'], status, cll.from_user.id, tz)
        if callback_data['level'] == '2':
            await cll.message.edit_text(**await packer.get_level_2(function, cll))

        elif callback_data['level'] == '3':
            await cll.message.edit_text(**await packer.get_level_3(function, cll, state), disable_web_page_preview=True)

        elif callback_data['level'] == '4':
            await cll.message.edit_text(**await packer.get_level_4(function, cll, state), disable_web_page_preview=True)

        elif callback_data['level'] == '5':
            ex_option = False
            if callback_data['action'] == "start_packaging":
                await save_fsm_data(state, order_description=cll.message.html_text)
                await packer.start_package(state, cll, tz)
                ex_option = True
            await cll.message.edit_text(**await packer.get_level_5(function, state, cll, first=ex_option),
                                        text=(await get_fsm_data(state, ["order_description"]))["order_description"],
                                        disable_web_page_preview=True)

        elif callback_data['level'] == '6':
            await save_fsm_data(state, text=cll.message.html_text)
            await cll.message.edit_text(**await packer.get_level_6(function, cll, state))

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
