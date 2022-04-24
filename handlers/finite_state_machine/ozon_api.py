from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from loader import dp
from states import fsm
from keyboards.inline import creator, moderator
from utils.formate_button import BackButton
from utils.message import del_msg, edit_current_msg
from utils.db import sql


back_btn = BackButton()


async def start_create_new_seller(chat_id: int, callback: dict, state):
    await fsm.NewSeller.town.set()
    msg_id = await sql.get_last_msg(chat_id)
    back = await (back_btn.functions[callback['@']])[0](callback['@'])
    async with state.proxy() as data:
        data['button'], data['msg_id'], data['chat_id'], data['inviter'] = back, msg_id, chat_id, callback['@']

    text = 'Добавление нового ключа API\nВведите город\nПример: Москва 1'
    await edit_current_msg(text, back, chat_id, msg_id)


@dp.message_handler(state=fsm.NewSeller.town)
async def new_seller_id(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['seller_name'], back, msg_id = msg.text, data['button'], int(data['msg_id'])
    await fsm.NewSeller.next()

    text = 'Добавление нового ключа API\nВведите ID продавца\nПример: 123456'
    await edit_current_msg(text, back, msg.chat.id, msg_id)
    await del_msg(msg)


@dp.message_handler(state=fsm.NewSeller.seller_id)
async def new_api_key(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['seller_id'], back, msg_id = msg.text, data['button'], int(data['msg_id'])
    await fsm.NewSeller.next()
    text = 'Добавление нового ключа склада\nВведите ID склада\nПример: 80006746352637'
    await edit_current_msg(text, back, msg.chat.id, msg_id)
    await del_msg(msg)


@dp.message_handler(state=fsm.NewSeller.warehouse_id)
async def new_api_key(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['warehouse_id'], back, msg_id = int(msg.text), data['button'], int(data['msg_id'])
    await fsm.NewSeller.next()
    text = 'Добавление нового ключа API\nВведите API ключ'
    await edit_current_msg(text, back, msg.chat.id, msg_id)
    await del_msg(msg)


@dp.message_handler(state=fsm.NewSeller.api_key)
async def new_time_zone(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['api_key'], back, msg_id = msg.text, data['button'], int(data['msg_id'])
    await fsm.NewSeller.next()

    text = 'Добавление нового ключа API\nВведите временную зону\nПример: Europe/Moscow'
    await edit_current_msg(text, back, msg.chat.id, msg_id)
    await del_msg(msg)


@dp.message_handler(state=fsm.NewSeller.timezone)
async def new_seller_tg_chat(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['timezone'], back, msg_id = msg.text, data['button'], int(data['msg_id'])
    await fsm.NewSeller.next()

    text = 'Добавление нового ключа API\nВведите номер чата для уведомлений\nПример: -423456789'
    await edit_current_msg(text, back, msg.chat.id, msg_id)
    await del_msg(msg)


@dp.message_handler(state=fsm.NewSeller.log_chat_id)
async def new_seller_tg_chat(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['log_chat_id'], back, msg_id = msg.text, data['button'], int(data['msg_id'])
    await fsm.NewSeller.next()

    text = 'Добавление нового ключа API\nВведите номер основного канала\nПример: -100423456789'
    await edit_current_msg(text, back, msg.chat.id, msg_id)
    await del_msg(msg)


@dp.message_handler(state=fsm.NewSeller.log_channel_id)
async def finish_create_new_seller(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['log_channel_id'], inviter, msg_id = msg.text, data['inviter'], int(data['msg_id'])
        await sql.create_new_api(data)

    func = creator.get_bot_level_3 if inviter == 'creator' else moderator.get_api_sellers_menu
    await state.finish()
    await edit_current_msg(**await func(inviter), chat_id=msg.chat.id, msg_id=msg_id)
    await del_msg(msg)


async def start_update_api_key(chat_id: int, callback: dict, state):
    await fsm.NewAPIKey.new_api_key.set()
    msg_id = await sql.get_last_msg(chat_id)

    async with state.proxy() as data:
        data['seller'], data['item'] = callback['seller'], callback['item']
        data['chat_id'], data['msg_id'], data['inviter'] = chat_id, msg_id, callback['@']

    text = 'Добавление нового ключа API\nВведите API ключ'
    await edit_current_msg(text, await back_btn.functions[callback['@']][1](), chat_id, msg_id)


@dp.message_handler(state=fsm.NewAPIKey.new_api_key)
async def finish_update_api_key(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        callback = data
    await sql.update_api_key(str(msg.text), int(callback['seller']))

    await state.finish()
    await edit_current_msg(**await creator.get_bot_level_3(callback["inviter"]),
                           chat_id=msg.chat.id, msg_id=int(callback['msg_id']))
    await del_msg(msg)
