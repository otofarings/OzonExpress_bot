from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.handler import SkipHandler
from aiogram.types import Message, CallbackQuery
from aiogram.utils.exceptions import MessageNotModified

from loader import dp
from states.fsm import Geo
from data.condition import FUNCTION
from keyboards.inline import collector
from utils.db_api.message import del_old_msg, del_msg, update_msg, push_info_msg


@dp.message_handler(CommandStart())
async def start_collector(msg: Message, function: str, status):
    """
    Menu: Main
    Option: /start
    """
    if function == FUNCTION['collector']:
        new_msg = await msg.answer(**await collector.get_main_menu(status))

        await update_msg(new_msg)
        await del_msg(msg)
    else:
        raise SkipHandler


@dp.message_handler(content_types=['location'], state=[Geo.geo])
async def get_geo(msg: Message, function, status, state: FSMContext, tz: str):
    if function == FUNCTION['collector']:
        if status in ['на смене', 'не на смене']:
            async with state.proxy() as data:
                action_, status_ = data['action'], data['status']

            status = await collector.check_action_menu(msg.chat.id, action_, status_, tz, location=msg.location)
            new_msg = await msg.answer(**await collector.get_main_menu(status))

            await state.finish()

        else:
            raise SkipHandler

        await update_msg(new_msg)
        await del_msg(msg)

    else:
        raise SkipHandler


@dp.message_handler(state=[Geo.geo])
async def get_geo_back(msg: Message, function, status, state: FSMContext):
    if function == FUNCTION['collector']:
        if msg.text == 'Назад':
            if status in ['на смене', 'не на смене']:
                async with state.proxy() as data:
                    status_ = data['status']

                new_msg = await msg.answer(**await collector.get_main_menu(status_))

                await state.finish()

            else:
                raise SkipHandler

            await update_msg(new_msg)
            await del_msg(msg)

    else:
        raise SkipHandler


@dp.callback_query_handler(collector.callback_data.filter(menu='main'), state='*')
async def open_main_menu(cll: CallbackQuery, callback_data: dict, tz: str, status, state: FSMContext):
    """
    Menu: Main
    """
    try:
        if (callback_data['action'] in ['start', 'finish']) and (status in ['на смене', 'не на смене']):
            await Geo.geo.set()

            async with state.proxy() as data:
                data['action'], data['status'] = callback_data['action'], status

            new_msg = await cll.message.answer(**await collector.check_location())
            await update_msg(new_msg)
            await del_msg(cll.message)

        else:
            status = await collector.check_action_menu(cll.message.chat.id, callback_data['action'], status, tz)

            if callback_data['action'] == 'close':
                await del_old_msg(cll.from_user.id, cll.message.message_id)

            else:
                await cll.message.edit_text(**await collector.get_main_menu(status))
                await dp.bot.answer_callback_query(cll.id)

    except MessageNotModified:
        return True


@dp.callback_query_handler(collector.callback_data.filter(menu='order'), state='*')
async def open_bot_menu(cll: CallbackQuery, callback_data: dict, tz: str, state: FSMContext):
    """
    Menu: Order
    """
    try:
        level, action, option = callback_data['level'], callback_data['action'], callback_data['option']

        if level == '2':
            await cll.message.edit_text(**await collector.open_start_menu(cll, tz))

        elif level == '3':
            await cll.message.edit_text(**await collector.open_orders_menu(cll, state, action),
                                        disable_web_page_preview=True)

        elif level == '4':
            await cll.message.edit_text(**await collector.get_order_menu(callback_data, state),
                                        disable_web_page_preview=True)

        elif level == '5':
            await cll.message.edit_reply_markup(**await collector.get_package_order_menu(callback_data, cll, tz))

        elif level == '6':
            if action == 'cancel':
                await cll.message.edit_text(**await collector.get_reasons_for_cancel_menu(cll, state))

            elif action == 'back' or action == 'future':
                if option == "402":
                    await push_info_msg(cll, 'Опция временно не доступна!')
                await cll.message.edit_text(**await collector.get_reasons_for_cancel_menu(state=state))

            else:
                await cll.message.edit_text(**await collector.get_product_id_menu(cll, state))

        elif level == '7':
            if action == 'open':
                await cll.message.edit_text(**await collector.get_pre_complete_menu(cll, state))
            else:
                await cll.message.edit_text(**await collector.get_pre_complete_menu(state=state))

        elif level == '8':
            await cll.message.edit_text(**await collector.get_complete_menu(cll, tz))

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)
