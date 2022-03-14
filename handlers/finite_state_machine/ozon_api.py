from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from loader import dp
from states import fsm
from keyboards.inline import creator, moderator
from utils.message import del_msg
from utils.db import sql
from utils.ozon_express_api.request import get_warehouses_list


async def start_create_new_seller(chat_id: int, callback: dict, state):
    await fsm.NewSeller.town.set()

    msg_id = await sql.get_last_msg(chat_id)

    func = creator.get_api_create_back_menu if callback['@'] == 'creator' else moderator.get_api_create_back_menu
    back_button = await func()

    async with state.proxy() as data:
        data['inviter'] = callback['@']
        data['button'], data['msg_id'], data['chat_id'] = back_button, msg_id, chat_id
    await dp.bot.edit_message_text(text='Добавление нового ключа API\nВведите город\nПример: Москва 1',
                                   reply_markup=back_button,
                                   chat_id=chat_id,
                                   message_id=msg_id)


@dp.message_handler(state=fsm.NewSeller.town)
async def new_seller_id(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['seller_name'], back_button, msg_id = msg.text, data['button'], int(data['msg_id'])
    await fsm.NewSeller.next()
    await dp.bot.edit_message_text(text='Добавление нового ключа API\nВведите Seller ID\nПример: 123456',
                                   reply_markup=back_button,
                                   chat_id=msg.chat.id,
                                   message_id=msg_id)
    await del_msg(msg)


@dp.message_handler(state=fsm.NewSeller.seller_id)
async def new_api_key(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['seller_id'], back_button, msg_id = int(msg.text), data['button'], int(data['msg_id'])
    await fsm.NewSeller.next()
    await dp.bot.edit_message_text(text='Добавление нового ключа API\nВведите API ключ',
                                   reply_markup=back_button,
                                   chat_id=msg.chat.id,
                                   message_id=msg_id)
    await del_msg(msg)


@dp.message_handler(state=fsm.NewSeller.api_key)
async def new_time_zone(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['api_key'], back_button, msg_id = msg.text, data['button'], int(data['msg_id'])
    await fsm.NewSeller.next()
    await dp.bot.edit_message_text(text='Добавление нового ключа API\nВведите временную зону\nПример: Europe/Moscow',
                                   reply_markup=back_button,
                                   chat_id=msg.chat.id,
                                   message_id=msg_id)
    await del_msg(msg)


@dp.message_handler(state=fsm.NewSeller.timezone)
async def new_seller_tg_chat(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['timezone'], back_button, msg_id = msg.text, data['button'], int(data['msg_id'])

    await fsm.NewSeller.next()
    await dp.bot.edit_message_text(text='Добавление нового ключа API\nВведите номер чата для уведомлений\nПример: -423456789',
                                   reply_markup=back_button,
                                   chat_id=msg.chat.id,
                                   message_id=msg_id)
    await del_msg(msg)


@dp.message_handler(state=fsm.NewSeller.log_chat_id)
async def finish_create_new_seller(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['log_chat_id'], inviter, msg_id = msg.text, data['inviter'], int(data['msg_id'])
        data['warehouse_id'] = await get_warehouses_list(data["seller_id"], data["api_key"])
        await sql.create_new_api(data)
    func = creator.get_api_sellers_menu if inviter == 'creator' else moderator.get_api_sellers_menu
    await dp.bot.edit_message_text(**await func(),
                                   chat_id=msg.chat.id,
                                   message_id=msg_id)
    await state.finish()
    await del_msg(msg)


async def start_update_api_key(chat_id: int, callback: dict, state):
    await fsm.NewAPIKey.new_api_key.set()
    msg_id = await sql.get_last_msg(chat_id)
    async with state.proxy() as data:
        data['seller'], data['item'] = callback['seller'], callback['item']
        data['chat_id'], data['msg_id'] = chat_id, msg_id
    await dp.bot.edit_message_text(text=f'Добавление нового ключа API\nВведите API ключ',
                                   reply_markup=await creator.get_api_replace_back_menu(callback),
                                   chat_id=chat_id,
                                   message_id=msg_id)


@dp.message_handler(state=fsm.NewAPIKey.new_api_key)
async def finish_update_api_key(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        callback = data
    await sql.update_api_key(str(msg.text), int(callback['seller']))
    await dp.bot.edit_message_text(**await creator.get_api_seller_menu(callback),
                                   chat_id=msg.chat.id,
                                   message_id=int(callback['msg_id']))
    await state.finish()
    await del_msg(msg)
