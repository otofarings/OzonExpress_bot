from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.handler import SkipHandler
from aiogram.types import Message, CallbackQuery
from aiogram.utils.exceptions import MessageNotModified

from loader import dp
from states.fsm import Geo, PreviousMenu
from data.condition import FUNCTION
from keyboards.inline import courier
from utils.db_api.message import del_old_msg, del_msg, update_msg, push_info_msg


@dp.message_handler(CommandStart())
async def start_courier(msg: Message, function, status):
    """
    Menu: Main
    Option: /start
    """
    if function == FUNCTION['courier']:
        new_msg = await msg.answer(**await courier.get_main_menu(status))

        await update_msg(new_msg)
        await del_msg(msg)

    else:
        raise SkipHandler


@dp.message_handler(content_types=['location'], state=[Geo.geo, PreviousMenu.geo])
async def get_geo(msg: Message, function, status, state: FSMContext, tz: str):
    if function == FUNCTION['courier']:
        if status in ['на смене', 'не на смене']:
            async with state.proxy() as data:
                action_, status_ = data['action'], data['status']

            status = await courier.check_action_menu(msg.chat.id, action_, status_, tz, msg.location)
            new_msg = await msg.answer(**await courier.get_main_menu(status))

            await state.finish()

        elif status in ['доставляет']:
            async with state.proxy() as data:
                reply_markup_, callback_ = data['reply_markup'], data['callback']

            new_msg = await msg.answer(**await courier.get_result_delivering_menu(tz, reply_markup=reply_markup_,
                                                                                  callback=callback_,
                                                                                  tg_id=msg.chat.id,
                                                                                  location=msg.location))

            await PreviousMenu.back_menu.set()

        else:
            raise SkipHandler

        await update_msg(new_msg)
        await del_msg(msg)

    else:
        raise SkipHandler


@dp.message_handler(state=[Geo.geo, PreviousMenu.geo])
async def get_geo_back(msg: Message, function, status, state: FSMContext):
    if function == FUNCTION['courier']:
        if msg.text == 'Назад':
            if status in ['на смене', 'не на смене']:
                async with state.proxy() as data:
                    status_ = data['status']

                new_msg = await msg.answer(**await courier.get_main_menu(status_))

                await state.finish()

            elif status in ['доставляет']:
                async with state.proxy() as data:
                    text_, reply_markup_ = data['text'], data['reply_markup']

                new_msg = await msg.answer(text=text_, reply_markup=reply_markup_)

                await PreviousMenu.back_menu.set()

            else:
                raise SkipHandler

            await update_msg(new_msg)
            await del_msg(msg)

    else:
        raise SkipHandler


@dp.callback_query_handler(courier.callback_data.filter(menu='main'))
async def open_main_menu(cll: CallbackQuery, callback_data: dict, tz: str, status, state: FSMContext):
    """
    Menu: Main
    """
    try:
        await state.finish()
        if (callback_data['action'] in ['start', 'finish']) and (status in ['на смене', 'не на смене']):
            await Geo.geo.set()

            async with state.proxy() as data:
                data['action'], data['status'] = callback_data['action'], status

            new_msg = await cll.message.answer(**await courier.check_location())
            await update_msg(new_msg)
            await del_msg(cll.message)

        else:
            status = await courier.check_action_menu(cll.message.chat.id, callback_data['action'], status, tz)

            if callback_data['action'] == 'close':
                await del_old_msg(cll.from_user.id, cll.message.message_id)

            else:
                await cll.message.edit_text(**await courier.get_main_menu(status))
                await dp.bot.answer_callback_query(cll.id)

    except MessageNotModified:
        return True


@dp.callback_query_handler(courier.callback_data.filter(menu='order'), state='*')
async def open_bot_menu(cll: CallbackQuery, callback_data: dict, tz: str, status, state: FSMContext):
    """
    Menu: Order
    """
    try:
        if callback_data['level'] == '2':
            await courier.check_action_menu(cll.message.chat.id, callback_data['action'], status, tz)
            await cll.message.edit_text(**await courier.open_start_menu(cll))

        elif callback_data['level'] == '3':
            await cll.message.edit_text(**await courier.get_order_menu(cll.from_user.id))

        elif callback_data['level'] == '4':
            if callback_data['action'] == 'open':
                await cll.message.edit_text(**await courier.get_order_info_menu(cll, state=state),
                                            disable_web_page_preview=True)

            elif callback_data['action'] == 'back':
                await cll.message.edit_text(**await courier.get_order_info_menu(state=state))

            elif callback_data['action'] == 'added':
                await push_info_msg(cll, 'Этот заказ является обязательным, т.к. ближайший по сроку исполнения')

            else:
                await cll.message.edit_reply_markup(**await courier.get_order_select_menu(cll))

        elif callback_data['level'] == '5':
            await cll.message.edit_text(**await courier.get_delivering_menu(cll, state, tz))

        elif callback_data['level'] == '6':
            if callback_data['action'] == 'open':
                await cll.message.edit_text(**await courier.get_delivering_order_info(cll, state=state),
                                            disable_web_page_preview=True)

            elif callback_data['action'] == 'back':
                await cll.message.edit_text(**await courier.get_delivering_order_info(state=state))

        elif callback_data['level'] == '7':
            if callback_data['action'] == 'open':
                await cll.message.edit_text(**await courier.get_delivering_menu_next(cll, state, tz))

            elif callback_data['action'] in ['delivered', 'return', 'no_call']:
                await PreviousMenu.geo.set()

                async with state.proxy() as data:
                    data['text'] = cll.message.html_text
                    data['reply_markup'] = cll.message.reply_markup
                    data['callback'] = cll.data

                new_msg = await cll.message.answer(**await courier.check_location())

                await update_msg(new_msg)
                await del_msg(cll.message)

                await courier.check_location()

            else:
                await cll.message.edit_text(**await courier.get_result_delivering_menu(tz, cll))

        elif callback_data['level'] == '8':
            await cll.message.edit_text(**await courier.get_complete_delivery_menu(cll))

    except MessageNotModified:
        return True

    finally:
        await dp.bot.answer_callback_query(cll.id)
