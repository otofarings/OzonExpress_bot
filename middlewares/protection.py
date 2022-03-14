import logging

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled

from loader import dp
from data.config import CREATOR_SECRET, CREATORS, DEBUG
from states.fsm import finish_state
from utils.db import sql


async def check_user_state(user_id: int):
    if user_id not in CREATORS:
        user_info = await sql.get_info_for_protection(user_id)

        if user_info:
            return user_info['function'], user_info['status'], user_info['state'], user_info['timezone']

        else:
            raise CancelHandler


async def check_start_command(msg):
    msg_lst = msg.text.split() if not msg.location else msg.reply_to_message.text.split()
    if msg_lst[0] == "/start":
        if len(msg_lst) == 1:
            await finish_state(msg.chat.id, msg.from_user.id)

        elif len(msg_lst) == 2:
            if len(msg_lst[1]) == 32:
                await sql.end_registration_new_user(msg_lst[-1], msg.from_user.id, msg.from_user.username)

            elif CREATOR_SECRET in msg_lst[1]:
                await sql.register_new_creator(msg_lst[-1], msg.from_user.id, msg.from_user.username)


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
        if update.message:
            msg = update.message

            if DEBUG:
                logging.info(msg)

            if msg.chat.type == 'private':
                await sql.log_entry(msg)
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

                await sql.log_entry(cbq, button_name)

                if cbq.data.split(':')[-1] == "pass":
                    raise CancelHandler

            else:
                raise CancelHandler

        else:
            raise CancelHandler

    @staticmethod
    async def on_process_callback_query(cll: types.CallbackQuery, data: dict):
        data['function'], data['status'], state, data['tz'] = await check_user_state(cll.message.chat.id)
        if (state != 'activated') and (cll.message.from_user.id not in CREATORS):
            raise CancelHandler

    @staticmethod
    async def on_process_message(msg: types.message.Message, data: dict):
        data['function'], data['status'], state, data['tz'] = await check_user_state(msg.chat.id)
        if (state != 'activated') and (msg.from_user.id not in CREATORS):
            raise CancelHandler
