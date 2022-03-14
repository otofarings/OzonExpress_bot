from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.handler import SkipHandler
from aiogram.types import Message, CallbackQuery
from aiogram.utils.exceptions import MessageNotModified

from data.condition import FUNCTION
from handlers.finite_state_machine.employee import start_create_new_user
from handlers.finite_state_machine.ozon_api import start_create_new_seller
from keyboards.inline import moderator
from loader import dp
from utils.message import update_msg, del_msg
from utils.db.users import del_user
from states.fsm import check_state


@dp.message_handler(CommandStart())
async def start_moderator(msg: Message, function):
    """
    Menu: Main
    Option: /start
    """
    if function == FUNCTION['moderator']:
        new_msg = await msg.answer(**await moderator.get_main_menu())
        await update_msg(dp, new_msg)
        await del_msg(msg)
    else:
        raise SkipHandler


@dp.callback_query_handler(moderator.callback_data.filter(menu='main'))
async def open_main_menu(cll: CallbackQuery, state: FSMContext):
    """
    Menu: Main
    """
    try:
        await state.finish()
        await cll.message.edit_text(**await moderator.get_main_menu())
        await dp.bot.answer_callback_query(cll.id)

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)


@dp.callback_query_handler(moderator.callback_data.filter(menu='bot'), state='*')
async def open_bot_menu(cll: CallbackQuery, callback_data: dict, state: FSMContext):
    """
    Menu: Bot
    """
    try:
        if callback_data['action'] == 'back':
            await check_state(state)

        if callback_data['level'] == '2':
            if callback_data['action'] == 'restart':
                pass

            elif callback_data['action'] in ['open', 'back']:
                await cll.message.edit_text(**await moderator.get_bot_menu())

        elif callback_data['level'] == '3':
            await cll.message.edit_text(**await moderator.get_api_sellers_menu(cll))

        elif callback_data['level'] == '4':
            if callback_data['action'] == 'add':
                await start_create_new_seller(chat_id=cll.from_user.id, callback=callback_data, state=state)

            else:
                await cll.message.edit_text(**await moderator.get_api_seller_menu(callback_data))

        await dp.bot.answer_callback_query(cll.id)

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)


@dp.callback_query_handler(moderator.callback_data.filter(menu='ozon'), state='*')
async def open_3_level(cll: CallbackQuery, callback_data: dict, state: FSMContext):
    """
    Menu: Ozon
    """
    try:
        if callback_data['action'] == 'back':
            await check_state(state)

        if callback_data['level'] == '2':
            await cll.message.edit_text(**await moderator.get_ozon_sellers_menu())

        elif callback_data['level'] == '3':
            await cll.message.edit_text(**await moderator.get_ozon_option_menu(callback_data))

        elif callback_data['level'] == '4':
            if callback_data['option'] == 'user':
                if callback_data['action'] == 'delete':
                    await del_user(int(callback_data['item_id']))

                await cll.message.edit_text(**await moderator.get_user_list_menu(callback_data))

            elif callback_data['option'] == 'stats':
                await cll.message.edit_text(**await moderator.get_stats_list_menu(callback_data))

        elif callback_data['level'] == '5':
            if callback_data['option'] == 'user':
                if callback_data['action'] == 'add':
                    await start_create_new_user(int(cll.from_user.id), callback_data, state)

                else:
                    await cll.message.edit_text(**await moderator.get_user_menu(callback_data))

            elif callback_data['option'] == 'stats':
                await cll.message.edit_text(**await moderator.get_selected_stat_menu(callback_data))

        await dp.bot.answer_callback_query(cll.id)

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)
