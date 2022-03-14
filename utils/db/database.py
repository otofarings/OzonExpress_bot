import logging
import json

import asyncpg
import asyncio

from data.config import DB_CONN_INFO, DEBUG
from .tables import tables


async def start_sql_bd() -> None:
    await db_query(dir_func=create_tables)
    return


async def db_query(func: str = None, sql: str = None, kwargs=None, dir_func=None):
    if DEBUG:
        logging.info(f"Запрос к БД: {sql},\nПереданные данные: {kwargs}")
    actions = {'execute': type_execute, 'fetch': type_fetch, 'fetch_json': type_fetch_json}
    return await asyncio.gather(actions[func](sql, kwargs)) if not dir_func else await asyncio.gather(dir_func())


async def type_execute(sql: str, kwarg: list) -> None:
    pool = await asyncpg.create_pool(**DB_CONN_INFO)
    conn = await pool.acquire()
    await conn.execute(sql, *kwarg)
    await conn.close()
    await pool.close()
    return


async def type_fetch(sql: str, kwarg: list):
    pool = await asyncpg.create_pool(**DB_CONN_INFO)
    conn = await pool.acquire()
    result = await conn.fetch(sql, *kwarg)
    logging.info(f"Результат запроса к БД: {result}") if DEBUG else None
    await conn.close()
    await pool.close()
    return result


async def type_fetch_json(sql: str, kwarg: list):
    pool = await asyncpg.create_pool(**DB_CONN_INFO)
    conn = await pool.acquire()
    await conn.set_type_codec('json', encoder=json.dumps, decoder=json.loads, schema='pg_catalog')
    result = await conn.fetchval(sql, *kwarg)
    await conn.close()
    await pool.close()
    return result


async def create_tables():
    pool = await asyncpg.create_pool(**DB_CONN_INFO)
    conn = await pool.acquire()

    for table in tables:
        await conn.execute(table)

    await conn.close()
    logging.info("База данных готова")
    return
