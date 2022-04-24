import uuid

from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from data.condition import FUNCTION
from data.config import BOT_NAME
from loader import dp
from states import fsm
from utils.message import del_msg, edit_current_msg
from utils.formate_button import BackButton
from utils.db import sql


user_btn = BackButton()


async def start_create_new_user(chat_id: int, callback: dict, state):
    await fsm.NewEmployee.new_name.set()

    back_menu = user_btn.functions[callback['@']]
    if callback['@'] == 'admin':
        new_func, back = callback['option'], await back_menu(callback['@'], callback['option'])
    else:
        new_func, back = callback['item'], (await back_menu[2](callback['@'], callback['seller'], callback['item']))
        async with state.proxy() as data:
            data['warehouse_id'] = callback['seller']

    msg_id = await sql.get_last_msg(chat_id)
    async with state.proxy() as data:
        data['new_func'], data['back'], data['msg_id'] = callback['item'], back, msg_id

    text = f"Добавление нового {FUNCTION[new_func]}а\nВведите ФИО\nПример: Иванов Иван Иванович"
    await edit_current_msg(text, back, chat_id, msg_id)


@dp.message_handler(state=fsm.NewEmployee.new_name)
async def create_new_user_name(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'], new_func, back, msg_id = msg.text, data['new_func'], data['back'], data['msg_id']

    if new_func == 'moderator':
        await state.finish()
        new_uuid = uuid.uuid4().hex
        await sql.register_new_moderator(new_uuid, msg.text, new_func, msg.chat.id)
        url = f"https://t.me/{BOT_NAME}?start={new_uuid}"
        text = f"Ссылка для входа нового Модератора:\n{url}"
        await edit_current_msg(text, back, msg.chat.id, msg_id)
    else:
        await fsm.NewEmployee.next()
        text = f"Введите номер телефона для {msg.text}\nПример: 79987654321"

    await edit_current_msg(text, back, msg.chat.id, msg_id)
    await del_msg(msg)


@dp.message_handler(state=fsm.NewEmployee.new_phone)
async def create_new_user_phone(msg: Message, state: FSMContext, function=None):
    async with state.proxy() as data:
        back, msg_id, name, new_func = data['back'], data['msg_id'], data['name'], data['new_func']

    if new_func in ['courier', 'packer'] and function == 'admin':
        new_uuid = uuid.uuid4().hex
        await sql.register_new_employee(new_uuid, name, new_func, msg.chat.id, msg.text)
        url = f'https://t.me/{BOT_NAME}?start={new_uuid}'
        text = f"Ссылка для входа нового {FUNCTION[new_func].capitalize()}а:\n{url}"
    else:
        async with state.proxy() as data:
            warehouse_id = data['warehouse_id']

        new_uuid = uuid.uuid4().hex
        await sql.register_new_admin(new_uuid, name, new_func, msg.chat.id, msg.text, int(warehouse_id))
        url = f'https://t.me/{BOT_NAME}?start={new_uuid}'
        text = f"Ссылка для входа нового {FUNCTION[new_func]}а:\n{url}"

    await state.finish()
    await edit_current_msg(text, back, msg.chat.id, msg_id)
    await del_msg(msg)


# @dp.message_handler(state=fsm.NewEmployee.new_warehouse_id)
# async def create_new_user_warehouse(msg: Message, state: FSMContext):
#     async with state.proxy() as data:
#         name, phone, new_func = data['name'], data['phone'], data['new_func']
#         back, msg_id, warehouse_id = data['back'], data['msg_id'], data['warehouse_id']
#
#     new_uuid = uuid.uuid4().hex
#     await sql.register_new_admin(new_uuid, name, new_func, msg.chat.id, phone, int(msg.text), int(warehouse_id))
#     url = f'https://t.me/{BOT_NAME}?start={new_uuid}'
#     text = f"Ссылка для входа нового {FUNCTION[new_func]}а:\n{url}"
#
#     await state.finish()
#     await edit_current_msg(text, back, msg.chat.id, msg_id)
#     await del_msg(msg)
