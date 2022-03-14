from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import SkipHandler
from aiogram.types import Message, CallbackQuery
from aiogram.utils.exceptions import MessageNotModified

from data.condition import FUNCTION
from loader import dp
from data.config import CREATORS
from keyboards.inline import creator
from utils.db.orders import get_orders
from utils.db.users import del_user
from utils.db import extra
from handlers.finite_state_machine.ozon_api import start_create_new_seller, start_update_api_key
from handlers.finite_state_machine.employee import start_create_new_user


@dp.message_handler(commands="start", chat_id=CREATORS)
async def start_creator(msg: Message):
    """
    Menu: Main
    Option: 1. Registers in DB if not exist
            2. Update last message_id in DB
    """
    new_msg = await msg.answer(**await creator.get_main_menu())
    await extra.update_msg_id(dp, new_msg)
    await extra.del_msg(msg)


@dp.callback_query_handler(creator.callback_data.filter(menu='main'))
async def open_main_menu(cll: CallbackQuery, state: FSMContext):
    """
    Menu: Main
    """
    await state.finish()
    await cll.message.edit_text(**await creator.get_main_menu())
    await dp.bot.answer_callback_query(cll.id)


@dp.callback_query_handler(creator.callback_data.filter(menu='bot'), state='*')
async def open_bot_menu(cll: CallbackQuery, callback_data: dict, state: FSMContext):
    """
    Menu: Bot
    """
    if callback_data['action'] == 'back':
        await extra.check_state(state)

    if callback_data['level'] == '2':
        if callback_data['action'] == 'restart':
            pass

        elif callback_data['action'] == 'turn_off':
            pass

        elif callback_data['action'] in ['open', 'back']:
            await cll.message.edit_text(**await creator.get_bot_menu())

    elif callback_data['level'] == '3':
        if callback_data['action'] == 'delete':
            await extra.del_api(int(callback_data['seller']))

        await cll.message.edit_text(**await creator.get_api_sellers_menu())

    elif callback_data['level'] == '4':
        if callback_data['action'] == 'add':
            await start_create_new_seller(chat_id=cll.from_user.id, callback=callback_data, state=state)

        else:
            await cll.message.edit_text(**await creator.get_api_seller_menu(callback_data))

    elif callback_data['level'] == '5':
        await start_update_api_key(chat_id=cll.from_user.id, callback=callback_data, state=state)

    await dp.bot.answer_callback_query(cll.id)


@dp.callback_query_handler(creator.callback_data.filter(menu='ozon'), state='*')
async def open_ozon_menu(cll: CallbackQuery, callback_data: dict, state: FSMContext):
    """
    Menu: Ozon
    """
    if callback_data['action'] == 'back':
        await extra.check_state(state)

    if callback_data['level'] == '2':
        await cll.message.edit_text(**await creator.get_ozon_sellers_menu())

    elif callback_data['level'] == '3':
        await cll.message.edit_text(**await creator.get_ozon_option_menu(callback_data))

    elif callback_data['level'] == '4':
        if callback_data['option'] == 'user':
            await cll.message.edit_text(**await creator.get_user_function_menu(callback_data))

        elif callback_data['option'] == 'order':
            await cll.message.edit_text(**await creator.get_order_state_menu(callback_data))

    elif callback_data['level'] == '5':
        if callback_data['option'] == 'user':
            if callback_data['action'] == 'delete':
                await del_user(int(callback_data['item_id']))

            if callback_data['action'] != 'pass':
                await cll.message.edit_text(**await creator.get_user_list_menu(callback_data))

        elif callback_data['option'] == 'order':
            if callback_data['action'] == 'delete':
                await get_orders(order_id=int(callback_data['item_id']), delete=True)

            elif callback_data['action'] == 'reset':
                await get_orders(order_id=int(callback_data['item_id']), reset=True)

            elif callback_data['action'] == 'cancel':
                pass

            await cll.message.edit_text(**await creator.get_order_list_menu(callback_data))

    elif callback_data['level'] == '6':
        if callback_data['option'] == 'user':
            if callback_data['action'] == 'add':
                await start_create_new_user(int(cll.from_user.id), callback_data, state)

            else:
                await cll.message.edit_text(**await creator.get_user_menu(callback_data))

        elif callback_data['option'] == 'order':
            await cll.message.edit_text(**await creator.get_order_menu(callback_data))

    await dp.bot.answer_callback_query(cll.id)


@dp.errors_handler(exception=MessageNotModified)
async def message_not_modified_handler(update, error):
    return True
