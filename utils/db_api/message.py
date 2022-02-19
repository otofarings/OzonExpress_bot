from contextlib import suppress

from aiogram.types import Message, CallbackQuery
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound

from loader import dp
from utils.db_api.database import db_query
from utils.proccess_time import get_time


async def update_msg(new_msg: Message):
    if new_msg:
        old_msg_id = await db_query(func='fetch',
                                    sql="""UPDATE employee SET msg_id = $1 WHERE tg_id = $2 AND state != $3
                                                   RETURNING (SELECT msg_id 
                                                              FROM employee WHERE tg_id = $2 AND state != $3);""",
                                    kwargs=[new_msg.message_id, new_msg.chat.id, 'удален'])

        if old_msg_id[0][0]['msg_id']:
            await del_old_msg(new_msg.chat.id, old_msg_id[0][0]['msg_id'])

    return


async def get_last_msg(tg_id: int):
    msg_id = await db_query(func='fetch',
                            sql="""SELECT msg_id FROM employee WHERE tg_id = $1 AND state != $2;""",
                            kwargs=[tg_id, 'удален'])
    return msg_id[0][0]['msg_id']


async def del_msg(msg: Message):
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await msg.delete()

    return


async def del_old_msg(chat_id, old_msg_id):
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await dp.bot.delete_message(chat_id, old_msg_id)
    return


async def push_info_msg(cll, text):
    await dp.bot.answer_callback_query(cll.id, text=text, show_alert=True)


async def save_callback(cll: CallbackQuery, tz):
    await db_query(func="execute",
                   sql="""INSERT INTO finite_state_machine 
                                  (tg_id, message_id, chat_id, text, entities, reply_markup, data, date)
                                  VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
                   kwargs=[cll.message.chat.id, cll.message.message_id, cll.message.chat.id, cll.message.text,
                                   cll.message.entities, cll.message.reply_markup, cll.data, await get_time(tz=tz)])
