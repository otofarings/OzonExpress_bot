import logging

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled

from loader import dp
from data.config import CREATOR_SECRET, CREATORS, DEBUG
from states.fsm import finish_state
from utils.db import sql


async def check_debug(obj) -> None:
    if DEBUG:
        logging.info(obj)


async def check_user_state(user_id: int):
    if user_id not in CREATORS:
        user_info = await sql.get_info_for_protection(user_id)
        if user_info:
            return user_info['function'], user_info['status'], user_info['state'], user_info['timezone']
        else:
            raise CancelHandler
    else:
        return "creator", "on_shift", "activated", "Europe/Moscow"


async def check_activating(tg_id: int, state: str):
    if (state != 'activated') and (tg_id not in CREATORS):
        raise CancelHandler
    else:
        return


async def check_start_command(msg) -> None:
    if not msg.location:
        msg_lst = msg.text.split()
        if msg_lst[0] == "/start":
            await check_start_msg_len(msg_lst, msg.chat.id, msg.from_user.id, msg.from_user.username)
    return


async def check_start_msg_len(msg_lst: list, chat_id: int, tg_id: int, username) -> None:
    if len(msg_lst) == 1:
        await finish_state(chat_id, tg_id)
    elif (len(msg_lst) == 2) and ((len(msg_lst[1]) == 32) or (CREATOR_SECRET in msg_lst[1])):
        sql_func = sql.end_registration_new_user if len(msg_lst[1]) == 32 else sql.register_new_creator
        await sql_func(msg_lst[-1], tg_id, username)


async def get_pushed_button_name(callback) -> str:
    for row in callback.message.reply_markup.inline_keyboard:
        for button in row:
            if button.callback_data == callback.data:
                return button.text
    return 'None'


async def update_msg_id(msg_id: int, old_msg_id: int) -> None:
    await sql.insert_message_id(msg_id, old_msg_id)


class CallbackAntiFlood(BaseMiddleware):
    def __init__(self):
        super(CallbackAntiFlood, self).__init__()

    @staticmethod
    async def on_pre_process_callback_query(cll: types.CallbackQuery, data: dict = None):
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
            await check_debug(update.message)
            if update.message.chat.type == 'private':
                await sql.log_entry(update.message)
                await check_start_command(update.message)
            else:
                if update.message.from_user.id in CREATORS:
                    await update.message.reply(update.message.chat.id)
                if (update.message.sender_chat.type == 'channel') and (update.message.from_user.id == 777000):
                    await update_msg_id(update.message.forward_from_message_id, update.message.message_id)
                raise CancelHandler

        elif update.callback_query:
            await check_debug(update.callback_query)
            if update.callback_query.message.chat.type == 'private':
                await sql.log_entry(update.callback_query, await get_pushed_button_name(update.callback_query))
                if update.callback_query.data.split(':')[-1] == "pass":
                    raise CancelHandler
            else:
                raise CancelHandler
        else:
            raise CancelHandler

    @staticmethod
    async def on_process_callback_query(cll: types.CallbackQuery, data: dict):
        data['function'], data['status'], state, data['tz'] = await check_user_state(cll.message.chat.id)
        await check_activating(cll.message.from_user.id, state)

    @staticmethod
    async def on_process_message(msg: types.message.Message, data: dict):
        data['function'], data['status'], state, data['tz'] = await check_user_state(msg.chat.id)
        await check_activating(msg.from_user.id, state)
