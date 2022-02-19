from contextlib import suppress

from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound

from states.fsm import PreviousMenu
from utils.db_api.database import db_query


# ****************************************Message****************************************
async def update_msg_id(dp, new_msg: Message):
    old_msg_id = await db_query(action='fetch',
                                sql_com='update_msg_id',
                                kwarg=[new_msg.message_id, new_msg.chat.id, 'удален'])
    if old_msg_id[0][0]['msg_id']:
        await del_old_msg(dp, new_msg.chat.id, old_msg_id[0][0]['msg_id'])


async def get_last_msg(tg_id: int):
    msg_id = await db_query(action='fetch',
                            sql_com='get_msg_id',
                            kwarg=[tg_id, 'удален'])
    return msg_id[0][0]['msg_id']


async def del_msg(msg: Message):
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await msg.delete()
    return


async def del_old_msg(dp, chat_id, old_msg_id):
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await dp.bot.delete_message(chat_id, old_msg_id)
    return


async def push_info_message(dp, cll, text):
    await dp.bot.answer_callback_query(cll.id, text=text, show_alert=True)


async def save_previous(text: str = None, markup=None, state=None, data_new=None, callback_data=None,
                        first: bool = True, last: bool = False, get: bool = False, menu: bool = False):
    if first:
        await PreviousMenu.back_menu.set()
    async with state.proxy() as data:
        if text:
            data['text'] = text
        if markup:
            data['reply_markup'] = markup
        if data_new:
            data['data'] = data_new
        if callback_data:
            data['callback_data'] = callback_data
    if get:
        async with state.proxy() as data:
            previous_menu = data
        if last:
            await state.finish()
        if menu:
            return {'reply_markup': previous_menu['reply_markup'], 'text': previous_menu['text']}
        if callback_data:
            return data['callback_data']
        else:
            return previous_menu['data']


# ****************************************API****************************************
async def create_new_api(dct: dict):
    await db_query(
        action='execute',
        sql_com='new_api',
        kwarg=[dct['seller_id'], dct['api_key'], dct['seller_name'],
               dct['timezone'], dct['log_chat_id'], dct['warehouse_id']]
    )
    return


async def get_api(seller_id: int):
    sellers = await db_query(
        action='fetch',
        sql_com='get_api',
        kwarg=[seller_id]
    )
    return sellers[0][0]


async def get_current_api(tg_id: int):
    sellers = await db_query(
        action='fetch',
        sql_com='get_current_api',
        kwarg=[tg_id]
    )
    return sellers[0][0]


async def get_all_api():
    sellers = await db_query(
        action='fetch',
        sql_com='get_all_api',
        kwarg=[]
    )
    return sellers[0]


async def update_api_key(api_key: str, seller_id: int):
    await db_query(
        action='execute',
        sql_com='update_api_key',
        kwarg=[str(api_key), int(seller_id)]
    )

    return


async def del_api(seller_id: int):
    await db_query(
        action='execute',
        sql_com='del_api',
        kwarg=[seller_id]
    )

    return


# ****************************************Stats****************************************
async def get_e_stat(seller_id: int):
    user_info = await db_query(
        action='fetch',
        sql_com='employee_stat_demo',
        kwarg=[seller_id]
    )
    return user_info[0][0]


# ****************************************State****************************************
async def check_state(state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    return


# ****************************************State****************************************
async def get_map_url(latitude, longitude):
    return f'https://yandex.ru/maps/?pt={longitude},{latitude}&z=17&l=map'


if __name__ == '__main__':
    pass
