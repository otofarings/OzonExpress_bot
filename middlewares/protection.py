import logging

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled

from loader import dp
from data.condition import USERS_STATE, FUNCTION
from data.config import CREATOR_SECRET, CREATORS, DEBUG
from states.fsm import finish_state
from utils.db_api.database import db_query
from utils.proccess_time import get_time


async def log_entry(new_obj, btn=None):
    obj = new_obj.message if btn else new_obj

    await db_query(func="execute",
                   sql="""INSERT INTO logs_button_clicks 
                                  (date, tg_id, chat_id, message_id, from_user_tg_id, 
                                  first_name, last_name, username, button_name, button_data)
                                  VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
                   kwargs=[await get_time(), new_obj.from_user.id, obj.chat.id, obj.message_id, obj.chat.id,
                                   obj.from_user.first_name, obj.from_user.last_name, obj.from_user.username,
                                   btn if btn else obj.text, new_obj.data if btn else 'None'])


async def check_user_state(user_id: int):
    if user_id not in CREATORS:
        user_info = await db_query(func="fetch",
                                   sql="""SELECT e.function, e.status, e.state, a.timezone FROM employee e, api a
                                                  WHERE a.seller_id=e.seller_id AND e.tg_id = $1 AND e.state = $2
                                                  AND a.seller_id IN (SELECT seller_id FROM employee
                                                                      WHERE tg_id = $1 AND state = $2);""",
                                   kwargs=[user_id, USERS_STATE["activated"]])

        if user_info[0][0]:
            return user_info[0][0]['function'], user_info[0][0]['status'], \
                   user_info[0][0]['state'], user_info[0][0]['timezone']

        else:
            raise CancelHandler


async def check_start_command(msg):
    print(msg)
    print(type(msg))
    msg_lst = msg.text.split() if not msg.location else msg.reply_to_message.text.split()
    if msg_lst[0] == "/start":
        if len(msg_lst) == 1:
            print('СБРОС состояния')
            await finish_state(msg.chat.id, msg.from_user.id)

        elif len(msg_lst) == 2:
            if len(msg_lst[1]) == 32:
                await db_query(func="execute",
                               sql="""WITH src AS (INSERT INTO employee_stat
                                                           (tg_id, orders_number, successful, unsuccessful)
                                                           VALUES($2, 0, 0, 0) ON CONFLICT (tg_id) DO NOTHING
                                                           RETURNING *)
                                          UPDATE employee
                                          SET tg_id = $2, username = $3, state = $4, begin_date = $6
                                          WHERE uuid = $1 AND state = $5;""",
                               kwargs=[msg_lst[-1], msg.from_user.id, msg.from_user.username,
                                               USERS_STATE["activated"], USERS_STATE["awaiting_activating"],
                                               await get_time()])

            elif CREATOR_SECRET in msg_lst[1]:
                await db_query(func="execute",
                               sql="""INSERT INTO employee 
                                              (uuid, tg_id, username, state, function, begin_date)
                                              VALUES($1, $2, $3, $4, $5, $6) ON CONFLICT (uuid) DO NOTHING;""",
                               kwargs=[msg_lst[-1], msg.from_user.id, msg.from_user.username,
                                       USERS_STATE["activated"], FUNCTION["creator"], await get_time()])


class CallbackAntiFlood(BaseMiddleware):

    def __init__(self):
        super(CallbackAntiFlood, self).__init__()

    @staticmethod
    async def on_pre_process_callback_query(cll: types.CallbackQuery, data: dict = None):
        """
        Этот обработчик вызывается, когда диспетчер получает обновление о нажатии кнопки
        """
        if cll.message:
            if cll.message.from_user:
                try:
                    await dp.throttle("settings_callback", rate=0.5)

                except Throttled as throttled:
                    if throttled.exceeded_count <= 2:
                        raise CancelHandler()


class Protection(BaseMiddleware):

    @staticmethod
    async def on_pre_process_update(update: types.Update, data: dict = None):
        print('OK')
        print(update)
        if update.message:
            msg = update.message

            if DEBUG:
                logging.info(msg)

            if msg.chat.type == 'private':
                await log_entry(msg)
                await check_start_command(msg)

            elif msg.chat.type != "private":
                if msg.from_user.id in CREATORS:
                    await msg.reply(msg.chat.id)

                raise CancelHandler

        elif update.callback_query:
            cbq = update.callback_query

            if DEBUG:
                logging.info(cbq)

            if cbq.message.chat.type == 'private':
                button_name = 'None'

                for row in cbq.message.reply_markup.inline_keyboard:
                    for button in row:
                        button_name = button.text if button.callback_data == cbq.data else 'None'

                await log_entry(cbq, btn=button_name)

                if cbq.data.split(':')[-1] == "pass":
                    raise CancelHandler

            else:
                raise CancelHandler

        else:
            raise CancelHandler

    @staticmethod
    async def on_process_callback_query(cll: types.CallbackQuery, data: dict):
        data['function'], data['status'], state, data['tz'] = await check_user_state(cll.message.chat.id)
        if (state != 'активирован') and (cll.message.from_user.id not in CREATORS):
            raise CancelHandler

    @staticmethod
    async def on_process_message(msg: types.message.Message, data: dict):
        print(msg)
        data['function'], data['status'], state, data['tz'] = await check_user_state(msg.chat.id)
        if (state != 'активирован') and (msg.from_user.id not in CREATORS):
            raise CancelHandler

