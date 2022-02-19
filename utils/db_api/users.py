import uuid

from data.config import BOT_NAME
from utils.db_api.database import db_query
from utils.proccess_time import get_time
from data.condition import FUNCTION, USERS_STATE


async def add_to_db(new_uuid: str, tg_id: int, username, superuser: bool = False):

    if superuser:
        await db_query(action="execute",
                       sql_com="new_creator",
                       kwarg=[new_uuid, tg_id, username, USERS_STATE["activated"],
                              FUNCTION["creator"], await get_time()])

    else:
        await db_query(action="execute",
                       sql_com="new_employee",
                       kwarg=[new_uuid, tg_id, username, USERS_STATE["activated"],
                              USERS_STATE["awaiting_activating"], await get_time()])

    return


async def get_user(seller_id: int = None, function: str = None, by_tg_id: int = None, tg_id: int = None,
                   user_id=None, change_stat: bool = False):
    if change_stat:
        users = await db_query(action='execute', sql_com='update_employee', kwarg=[tg_id])
    elif tg_id:
        if function:
            users = await db_query(action='fetch', sql_com='get_employee_special_v2', kwarg=[tg_id, function, 'удален'])
            return users[0]

        else:
            users = await db_query(action='fetch', sql_com='get_employee_special', kwarg=[tg_id, 'удален',
                                                                                          'ожидает активации'])
        return users[0]

    elif by_tg_id:
        user_info = await db_query(action='fetch', sql_com='get_employee_by_tg_id', kwarg=[by_tg_id])

        return user_info[0][0]

    elif user_id:
        user_info = await db_query(action='fetch', sql_com='get_employee_info', kwarg=[user_id])

        return user_info[0][0]

    elif function == 'модератор':
        users = await db_query(action='fetch', sql_com='get_moderator', kwarg=[function, 'удален'])

    else:
        users = await db_query(action='fetch', sql_com='get_employee', kwarg=[seller_id, function, 'удален'])

    return users[0]


async def get_users(tg_id: int = None, seller_id: int = None, function: str = None):
    if seller_id:
        users = await db_query(action='fetch', sql_com='get_employee', kwarg=[seller_id, function, 'удален'])
    elif tg_id:
        users = await db_query(action='fetch', sql_com='get_employee_special_v2', kwarg=[tg_id, function, 'удален'])
    else:
        users = ['']
    return users[0]


async def get_user_info(user_id: int = None, user_tg_id: int = None):
    if user_tg_id:
        user_info = await db_query(action='fetch', sql_com='get_employee_by_tg_id', kwarg=[user_tg_id])
    elif user_id:
        user_info = await db_query(action='fetch', sql_com='get_employee_info', kwarg=[user_id])
    else:
        user_info = ['']
    return user_info[0]


async def del_user(user_id: int):
    await db_query(action='execute',
                   sql_com='delete_employee',
                   kwarg=['удален', await get_time(), user_id])
    return


async def check_state(tg_id: int):

    user_info = await db_query(action="fetch",
                               sql_com="check_state",
                               kwarg=[tg_id, USERS_STATE["activated"]])
    return user_info[0][0] if user_info[0] else False


async def create_new(tg_id: int, name: str, function: str, phone: str = None,
                     warehouse_id: int = None, seller_id: int = None):
    new_uuid = uuid.uuid4().hex

    if function == 'модератор':
        await db_query(action='execute',
                       sql_com='create_moderator',
                       kwarg=[new_uuid, 'ожидает активации', name, function, tg_id])
    else:
        await db_query(action='execute',
                       sql_com='create_user',
                       kwarg=[new_uuid, warehouse_id, seller_id, name, phone, 'ожидает активации', function, tg_id])

    return f'https://t.me/{BOT_NAME}?start={new_uuid}'


if __name__ == "__main__":
    pass
