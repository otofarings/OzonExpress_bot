from datetime import timedelta, datetime
import pytz

import asyncio

from data.config import TIME_FORMAT


async def pause(sec: int) -> None:
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


async def get_diff(tz: str, start_):
    time_left = (await get_time(tz=tz) - (start_ - timedelta(minutes=6))).total_seconds() // 60
    return time_left


async def check_error_time(error_info, tz: str) -> bool:
    dif_sec = (await get_time(tz=tz) - error_info["date"]).seconds
    if ((dif_sec / 60 > 1) and (error_info["count"] > 5) and (error_info["count"] < 7)) or \
            ((dif_sec / 60 > 5) and (error_info["count"] > 25) and (error_info["count"] < 27)) or \
            ((dif_sec / 60 > 10) and (error_info["count"] > 50) and (error_info["count"] < 52)) or \
            ((dif_sec / 60 > 30) and (error_info["count"] > 150) and (error_info["count"] < 152)):
        return True
    else:
        return False


async def get_dt_for_polling(in_process_at_, shipment_date_, tz_: str) -> dict:
    in_process_at = await change_dt_api_format(in_process_at_, tz_) if type(in_process_at_) == str else in_process_at_
    shipment_date = await change_dt_api_format(shipment_date_, tz_) if type(shipment_date_) == str else shipment_date_

    return {"in_process_at": in_process_at,
            "shipment_date": shipment_date,
            "predicted_date": await get_predict_time_for_delivery(shipment_date, 24),
            "current_time": await get_time(tz=tz_)}


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
    return time_to_edit + timedelta(minutes=n)
