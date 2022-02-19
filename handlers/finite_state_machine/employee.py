import uuid

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from data.config import BOT_NAME
from loader import dp
from states import fsm
from keyboards.inline import creator, moderator, admin
from utils.db_api.extra import save_previous
from utils.db_api.database import db_query
from utils.db_api import message


async def start_create_new_user(chat_id: int, callback: dict, state):
    await fsm.NewEmployee.new_name.set()
    msg_id = await message.get_last_msg(chat_id)
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
    if new_func == 'модератор':
        await state.finish()

        new_uuid = uuid.uuid4().hex
        await db_query(func='execute',
                       sql="""INSERT INTO employee (uuid, state, name, function, added_by_id) 
                                      VALUES($1, $2, $3, $4, $5);""",
                       kwargs=[new_uuid, 'ожидает активации', msg.text, new_func, msg.chat.id])

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
    await message.del_msg(msg)


@dp.message_handler(state=fsm.NewEmployee.new_phone)
async def create_new_user_phone(msg: Message, state: FSMContext, function=None):
    async with state.proxy() as data:
        data['phone'], new_func = msg.text, data['new_func']
        back_button, msg_id, name = data['back'], data['msg_id'], data['name']

    if new_func in ['курьер', 'сборщик'] and function == 'админ':
        await state.finish()

        ex_id_data = await db_query(func='fetch',
                                    sql="""SELECT * FROM employee WHERE tg_id = $1;""",
                                    kwargs=[msg.chat.id])

        new_uuid = uuid.uuid4().hex

        await db_query(func='execute',
                       sql="""INSERT INTO employee 
                                      (uuid, warehouse_id, seller_id, name, phone, state, function, added_by_id)
                                      VALUES($1, $2, $3, $4, $5, $6, $7, $8);""",
                       kwargs=[new_uuid, ex_id_data[0][0]['warehouse_id'], ex_id_data[0][0]['seller_id'], name,
                                       msg.text, 'ожидает активации', new_func, msg.chat.id])

        url = f'https://t.me/{BOT_NAME}?start={new_uuid}'

        await dp.bot.edit_message_text(text=f'Ссылка для входа нового {new_func.capitalize()}а:\n{url}',
                                       reply_markup=back_button,
                                       chat_id=msg.chat.id,
                                       message_id=msg_id)

    else:
        await fsm.NewEmployee.next()
        await dp.bot.edit_message_text(text=f'Введите номер склада для {name}\n',
                                       reply_markup=back_button,
                                       chat_id=msg.chat.id,
                                       message_id=msg_id)
    await message.del_msg(msg)


@dp.message_handler(state=fsm.NewEmployee.new_warehouse_id)
async def create_new_user_warehouse(msg: Message, state: FSMContext):
    async with state.proxy() as data:
        name, phone, new_func, seller_id = data['name'], data['phone'], data['new_func'], data['seller_id']
        back_button, msg_id = data['back'], data['msg_id']

    new_uuid = uuid.uuid4().hex

    await db_query(func='execute',
                   sql="""INSERT INTO employee 
                                  (uuid, warehouse_id, seller_id, name, phone, state, function, added_by_id)
                                  VALUES($1, $2, $3, $4, $5, $6, $7, $8);""",
                   kwargs=[new_uuid, int(msg.text), int(seller_id), name,
                                   phone, 'ожидает активации', new_func, msg.chat.id])

    url = f'https://t.me/{BOT_NAME}?start={new_uuid}'

    await dp.bot.edit_message_text(text=f'Ссылка для входа нового {new_func}а:\n{url}',
                                   reply_markup=back_button,
                                   chat_id=msg.chat.id,
                                   message_id=msg_id)
    await state.finish()
    await message.del_msg(msg)


# async def send_request_geo(chat_id: int, cll, state):
#     await fsm.Geo.geo.set()
#
#     await save_previous(cll.message.html_text, cll.message.reply_markup, state, first=True)
#
#     keyboard = ReplyKeyboardMarkup()
#     keyboard.add(KeyboardButton("Предоставить свое текущее местоположение", request_location=True),
#                  KeyboardButton("Назад"))
#
#     msg_id = await message.get_last_msg(chat_id)
#     await dp.bot.edit_message_text(text=f'Для продолжения необходимо предоставить доступ к текущему местоположению',
#                                    reply_markup=keyboard,
#                                    chat_id=chat_id,
#                                    message_id=msg_id)
#
#
# @dp.message_handler(state=fsm.Geo.geo)
# async def get_geo(msg: Message, state: FSMContext):
#
#     await message.del_msg(msg)
#
#
# @dp.message_handler(state=fsm.Geo.geo, content_types=['location'])
# async def get_geo(msg: Message, state: FSMContext):
#     print(msg)
#     await state.finish()
#     await message.del_msg(msg)

