from datetime import timedelta, datetime
import pytz

import asyncio

from data.config import TIME_FORMAT


async def pause(sec):
    await asyncio.sleep(sec)
    return


async def get_time(n=None, minus: bool = False, plus: bool = False, tz: str = None, st=None):
    date_time = st if st else datetime.now(pytz.timezone(tz) if tz else None)
    if minus:
        result_time = date_time - timedelta(hours=n)
    elif plus:
        result_time = date_time + timedelta(hours=n)
    else:
        result_time = date_time

    return result_time.replace(tzinfo=None) if tz else result_time


async def change_dt_format(time_to_edit):
    return datetime.strptime(time_to_edit, TIME_FORMAT)


async def change_timezone(time_to_edit, tz: str = None):
    edited_time, current_date = await change_dt_format(time_to_edit), await get_time(tz=tz)
    # print(current_date, edited_time)
    # dif_time = round((current_date - edited_time).total_seconds() / 60)
    # print(dif_time)
    # count = 0
    # while dif_time % 60 != 0:
    #     dif_time += 1
    #     count += 1
    result_time = edited_time + timedelta(hours=7)
    return result_time


async def change_dt_api_format(time_to_edit, tz):
    edited_time = await change_timezone(time_to_edit, tz)
    return edited_time.replace(tzinfo=None)


async def get_predict_time_for_delivery(time_to_edit, n: int):
    result_time = time_to_edit + timedelta(hours=n)
    return result_time
