from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.exceptions import MessageNotModified

from loader import dp
from keyboards.inline import creator
from data.condition import CALLBACK
from utils.db.orders import get_orders
from utils.db.users import del_user
from handlers.finite_state_machine.ozon_api import start_create_new_seller, start_update_api_key
from handlers.finite_state_machine.employee import start_create_new_user


@dp.callback_query_handler(CALLBACK['creator'].filter(menu='bot'), state='*')
async def open_bot_menu(cll: CallbackQuery, callback_data: dict, function: str, tz: str, status, state: FSMContext):
    try:
        if callback_data['level'] == '2':
            if callback_data['action'] == 'restart':
                pass
            elif callback_data['action'] == 'turn_off':
                pass
            elif callback_data['action'] in ['open', 'back']:
                await cll.message.edit_text(**await creator.get_bot_level_2(function))

        elif callback_data['level'] == '3':
            await cll.message.edit_text(**await creator.get_bot_level_3(function, callback_data))

        elif callback_data['level'] == '4':
            if callback_data['action'] == 'add':
                await start_create_new_seller(chat_id=cll.from_user.id, callback=callback_data, state=state)
            else:
                await cll.message.edit_text(**await creator.get_bot_level_4(function, callback_data))

        elif callback_data['level'] == '5':
            await start_update_api_key(chat_id=cll.from_user.id, callback=callback_data, state=state)

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)


@dp.callback_query_handler(CALLBACK['creator'].filter(menu='ozon'), state='*')
async def open_ozon_menu(cll: CallbackQuery, callback_data: dict, function: str, tz: str, status, state: FSMContext):
    try:
        if callback_data['level'] == '2':
            await cll.message.edit_text(**await creator.get_ozon_level_2(function))

        elif callback_data['level'] == '3':
            await cll.message.edit_text(**await creator.get_ozon_level_3(function, callback_data))

        elif callback_data['level'] == '4':
            if callback_data['option'] == 'user':
                await cll.message.edit_text(**await creator.get_ozon_level_4_1(function, callback_data))

            elif callback_data['option'] == 'order':
                await cll.message.edit_text(**await creator.get_order_state_menu(callback_data))

        elif callback_data['level'] == '5':
            if callback_data['option'] == 'user':
                await cll.message.edit_text(**await creator.get_ozon_level_5_1(function, callback_data))

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
                    await cll.message.edit_text(**await creator.get_ozon_level_6_1(function, callback_data))

            elif callback_data['option'] == 'order':
                await cll.message.edit_text(**await creator.get_order_menu(callback_data))

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)
