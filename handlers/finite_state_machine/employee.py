import uuid

from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from data.condition import FUNCTION
from data.config import BOT_NAME
from loader import dp
from states import fsm
from keyboards.inline import creator, moderator, admin
from utils.message import del_msg
from utils.db import sql


async def start_create_new_user(chat_id: int, callback: dict, state):
    await fsm.NewEmployee.new_name.set()
    msg_id = await sql.get_last_msg(chat_id)
    if callback['@'] == 'admin':
        new_func, user = callback['option'], admin
        button_data = [new_func]
    else:
        new_func, seller_id = callback['item'], callback['seller']
        user = creator if callback['@'] == 'creator' else moderator
        button_data = [seller_id, 'user', new_func]
        async with state.proxy() as data:
            data['seller_id'] = seller_id
    back_button = await user.get_user_create_back_menu(*button_data)
    async with state.proxy() as data:
        data['new_func'], data['back'], data['msg_id'] = new_func, back_button, msg_id
    await dp.bot.edit_message_text(text=f'Добавление нового {new_func}а\nВведите ФИО\nПример: Иванов Иван Иванович',
                                   reply_markup=back_button,
                                   chat_id=chat_id,
                                   message_id=msg_id)


@dp.message_handler(state=fsm.NewEmployee.new_name)
async def create_new_user_name(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'], new_func, back_button, msg_id = msg.text, data['new_func'], data['back'], data['msg_id']

    if new_func == 'moderator':
        await state.finish()

        new_uuid = uuid.uuid4().hex
        await sql.register_new_moderator(new_uuid, msg.text, new_func, msg.chat.id)

        url = f'https://t.me/{BOT_NAME}?start={new_uuid}'
        await dp.bot.edit_message_text(text=f'Ссылка для входа нового Модератора:\n{url}',
                                       reply_markup=back_button,
                                       chat_id=msg.chat.id,
                                       message_id=msg_id)
    else:
        await fsm.NewEmployee.next()
        await dp.bot.edit_message_text(text=f'Введите номер телефона для {msg.text}\nПример: 79987654321',
                                       reply_markup=back_button,
                                       chat_id=msg.chat.id,
                                       message_id=msg_id)
    await del_msg(msg)


@dp.message_handler(state=fsm.NewEmployee.new_phone)
async def create_new_user_phone(msg: Message, state: FSMContext, function=None):
    async with state.proxy() as data:
        data['phone'], new_func = msg.text, data['new_func']
        back_button, msg_id, name = data['back'], data['msg_id'], data['name']

    if new_func in ['courier', 'packer'] and function == 'admin':
        await state.finish()

        new_uuid = uuid.uuid4().hex
        await sql.register_new_employee(new_uuid, name, new_func, msg.chat.id, msg.text)

        url = f'https://t.me/{BOT_NAME}?start={new_uuid}'
        await dp.bot.edit_message_text(text=f'Ссылка для входа нового {FUNCTION[new_func].capitalize()}а:\n{url}',
                                       reply_markup=back_button,
                                       chat_id=msg.chat.id,
                                       message_id=msg_id)

    else:
        await fsm.NewEmployee.next()
        await dp.bot.edit_message_text(text=f'Введите номер склада для {name}\n',
                                       reply_markup=back_button,
                                       chat_id=msg.chat.id,
                                       message_id=msg_id)
    await del_msg(msg)


@dp.message_handler(state=fsm.NewEmployee.new_warehouse_id)
async def create_new_user_warehouse(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        name, phone, new_func, seller_id = data['name'], data['phone'], data['new_func'], data['seller_id']
        back_button, msg_id = data['back'], data['msg_id']

    new_uuid = uuid.uuid4().hex
    await sql.register_new_admin(new_uuid, name, new_func, msg.chat.id, phone, int(msg.text), int(seller_id))

    url = f'https://t.me/{BOT_NAME}?start={new_uuid}'
    await dp.bot.edit_message_text(text=f'Ссылка для входа нового {FUNCTION[new_func]}а:\n{url}',
                                   reply_markup=back_button,
                                   chat_id=msg.chat.id,
                                   message_id=msg_id)
    await state.finish()
    await del_msg(msg)
