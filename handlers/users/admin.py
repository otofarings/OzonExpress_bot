from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.handler import SkipHandler
from aiogram.types import Message, CallbackQuery
from aiogram.utils.exceptions import MessageNotModified

from data.condition import FUNCTION
from handlers.finite_state_machine.employee import start_create_new_user
from loader import dp
from keyboards.inline import admin
from utils.db_api import message, extra
from utils.db_api.message import push_info_msg


@dp.message_handler(CommandStart())
async def start_admin(msg: Message, function):
    """
    Menu: Main
    Option: /start
    """
    if function == FUNCTION['admin']:
        new_msg = await msg.answer(**await admin.get_main_menu())
        await message.update_msg(new_msg)
        await message.del_msg(msg)
    else:
        raise SkipHandler


@dp.callback_query_handler(admin.callback_data.filter(menu='main'))
async def open_main_menu(cll: CallbackQuery):
    """
    Menu: Main
    """
    try:
        new_msg = await cll.message.edit_text(**await admin.get_main_menu())
        print(new_msg)

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)


@dp.callback_query_handler(admin.callback_data.filter(menu='order'), state='*')
async def open_order_menu(cll: CallbackQuery, callback_data: dict, tz: str, state: FSMContext):
    """
    Menu: Order
    """
    try:
        if callback_data['level'] == '2':
            await cll.message.edit_text(**await admin.get_preorders_menu(cll))

        elif callback_data['level'] == '3':
            await cll.message.edit_text(**await admin.get_orders_menu(cll, tz))

        elif callback_data['level'] == '4':
            if callback_data['action'] == 'assign':
                pass

            await cll.message.edit_text(**await admin.get_orders_list_menu(dp, cll),
                                        disable_web_page_preview=True)

        elif callback_data['level'] == '5':
            if callback_data['action'] == 'reassign':
                await cll.message.edit_text(**await admin.get_users_for_reassign_menu(cll))

            elif callback_data['action'] == 'cancel':
                await cll.message.edit_text(**await admin.get_reasons_for_cancel_menu(callback_data))

        elif callback_data['level'] == '6':
            if callback_data['action'] == 'open':
                await cll.message.edit_text(**await admin.get_user_for_reassign_menu(cll, state))

            else:
                await cll.message.edit_text(**await admin.get_user_for_reassign_menu(state=state))

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)


@dp.callback_query_handler(admin.callback_data.filter(menu='delivery'), state='*')
async def open_courier_menu(cll: CallbackQuery, callback_data: dict, tz: str, state: FSMContext):
    """
        Menu: Order
        """
    try:
        level, action, option = callback_data['level'], callback_data['action'], callback_data['option']
        if level == '2':
            await cll.message.edit_text(**await admin.open_courier_start_menu(cll, dp))
        elif level == '3':
            await cll.message.edit_text(**await admin.get_courier_order_menu(cll.from_user.id))
        elif level == '4':
            if action == 'open':
                await cll.message.edit_text(**await admin.get_courier_order_info_menu(cll, state=state),
                                            disable_web_page_preview=True)
            elif action == 'back':
                await cll.message.edit_text(**await admin.get_courier_order_info_menu(state=state))
            elif action == 'added':
                await push_info_msg(cll, 'Этот заказ является обязательным, т.к. ближайший по сроку исполнения')
            else:
                await cll.message.edit_reply_markup(**await admin.get_courier_order_select_menu(cll))
        elif level == '5':
            await cll.message.edit_text(**await admin.get_courier_delivering_menu(cll, state, dp, tz))
        elif level == '6':
            if action == 'open':
                await cll.message.edit_text(**await admin.get_courier_delivering_order_info(cll, state=state),
                                            disable_web_page_preview=True)
            elif action == 'back':
                await cll.message.edit_text(**await admin.get_courier_delivering_order_info(state=state))
        elif level == '7':
            if action == 'open':
                await cll.message.edit_text(**await admin.get_courier_delivering_menu_next(cll, state))
            else:
                await cll.message.edit_text(**await admin.get_courier_result_delivering_menu(cll, dp, tz))
        elif level == '8':
            await cll.message.edit_text(**await admin.get_courier_complete_delivery_menu(cll))

    except MessageNotModified:
        return True
    finally:
        await dp.bot.answer_callback_query(cll.id)


@dp.callback_query_handler(admin.callback_data.filter(menu='package'), state='*')
async def open_packer_menu(cll: CallbackQuery, callback_data: dict, tz: str, state: FSMContext):
    """
    Menu: Order
    """
    try:
        level, action, option = callback_data['level'], callback_data['action'], callback_data['option']

        if level == '2':
            await cll.message.edit_text(**await admin.open_packer_start_menu(cll, dp, tz))

        elif level == '3':
            await cll.message.edit_text(**await admin.open_packer_orders_menu(cll, state, action),
                                        disable_web_page_preview=True)

        elif level == '4':
            await cll.message.edit_text(**await admin.get_packer_order_menu(callback_data, state),
                                        disable_web_page_preview=True)

        elif level == '5':
            await cll.message.edit_reply_markup(**await admin.get_packer_package_order_menu(callback_data, cll, dp, tz))

        elif level == '6':
            if action == 'cancel':
                await cll.message.edit_text(**await admin.get_packer_reasons_for_cancel_menu(cll, state))

            elif action == 'back' or action == 'future':
                if option == "402":
                    await message.push_info_msg(cll, 'Опция временно не доступна!')
                await cll.message.edit_text(**await admin.get_packer_reasons_for_cancel_menu(state=state))

            else:
                await cll.message.edit_text(**await admin.get_packer_product_id_menu(cll, state))

        elif level == '7':
            await cll.message.edit_text(**await admin.get_packer_complete_menu(cll, dp, state, tz))

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)


@dp.callback_query_handler(admin.callback_data.filter(menu='user'), state='*')
async def open_user_menu(cll: CallbackQuery, callback_data: dict, state: FSMContext):
    """
    Menu: User
    """
    try:
        if callback_data['level'] == '2':
            await cll.message.edit_text(**await admin.get_employee_menu())

        elif callback_data['level'] == '3':
            if callback_data['action'] == 'delete':
                pass

            elif callback_data['action'] == 'cancel':
                await extra.check_state(state)

            await cll.message.edit_text(**await admin.get_users_menu(cll))

        elif callback_data['level'] == '4':
            if callback_data['action'] == 'add':
                await start_create_new_user(chat_id=cll.from_user.id, callback=callback_data, state=state)

            else:
                await cll.message.edit_text(**await admin.get_user_menu(callback_data))

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)
