import logging

import asyncpg
import asyncio
import json

from loader import config
from data.config import DEBUG


async def db_query(func: str = None, sql: str = None, kwargs=None, dir_func=None):
    if DEBUG:
        logging.info(f"Запрос к БД: {sql},\nПереданные данные: {kwargs}")
    actions = {'execute': type_execute, 'fetch': type_fetch, 'fetch_json': type_fetch_json}
    return await asyncio.gather(actions[func](sql, kwargs)) if not dir_func else await asyncio.gather(dir_func())


async def type_execute(sql: str, kwarg: list):
    pool = await asyncpg.create_pool(**config.DB_CONN_INFO)
    conn = await pool.acquire()
    await conn.execute(sql, *kwarg)
    await conn.close()
    await pool.close()
    return


async def type_fetch(sql: str, kwarg: list):
    pool = await asyncpg.create_pool(**config.DB_CONN_INFO)
    conn = await pool.acquire()
    result = await conn.fetch(sql, *kwarg)
    logging.info(f"Результат запроса к БД: {result}") if DEBUG else None
    await conn.close()
    await pool.close()
    return result


async def type_fetch_json(sql: str, kwarg: list):
    pool = await asyncpg.create_pool(**config.DB_CONN_INFO)
    conn = await pool.acquire()
    await conn.set_type_codec('json', encoder=json.dumps, decoder=json.loads, schema='pg_catalog')
    result = await conn.fetchval(sql, *kwarg)
    await conn.close()
    await pool.close()
    return result
