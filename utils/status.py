import logging

import aiogram.utils.markdown as fmt

from loader import dp
from data.condition import FUNCTION
from data.config import MODER_LOGS, DEBUG
from utils.db import sql
from utils.proccess_time import get_time


async def change_status(function: str, action: str, status: str, tg_id: int, tz: str, location: dict = None) -> str:
    new_status = status

    if function in ["admin", "packer", "courier"]:

        if action in ["reserve_back", "update"]:
            new_status = "on_shift"
            await reserve_back(tg_id, status)
        elif (action == "start") and (status == "not_on_shift"):
            new_status = "on_shift"
            await send_info_log(tg_id, "Начал смену")
        elif (action == "finish") and (status == "on_shift"):
            new_status = "not_on_shift"
            await send_info_log(tg_id, "Завершил смену")

        elif action == "ex_reserve_delivery":
            new_status = "reserve_delivery"

        elif (action == "reserve_package") and (status == "on_shift"):
            new_status = "reserve_package"
        elif (action == "reserve_delivery") and (status == "on_shift"):
            new_status = "reserve_delivery"

        elif (action == "start_packaging") and (status == "reserve_package"):
            new_status = "packaging"
        elif action == "complete":
            new_status = "on_shift"
            if function == "courier":
                await send_info_log(tg_id, "Вернулся на склад")

        elif action == "start_cancel":
            new_status = "cancelling"
        elif (action == "finish_cancel") and (status == "cancelling"):
            new_status = "packaging" if function == "packer" else "on_shift"

        elif action == "start_weight":
            new_status = "weighting"
        elif action == "finish_weight":
            new_status = "packaging"

        if status != new_status:
            current_time = await get_time(tz=tz)
            await write_new_status([tg_id, new_status, current_time], location)
            logging.info(f"{current_time}| {function} : {status} -> {new_status}")

    return new_status


async def check_first_line_status(status: str) -> (str, str, str):
    if status == "reserve_package":
        return ["reserved_by_packer", "awaiting_packaging", "packer_id"]
    elif status in ["reserve_delivery", "ex_reserve_delivery"]:
        return ["reserved_by_deliver", "awaiting_deliver", "deliver_id"]
    else:
        return ["", "", ""]


async def send_info_log(chat_id: int, action: str, msg_to_reply: int = None, ex_option: str = None) -> None:
    api = await sql.get_api_info(chat_id)
    user_info = await sql.get_user_info(tg_id=chat_id)
    text = fmt.text(ex_option if ex_option else "",
                    fmt.text(fmt.hbold(f"{str(FUNCTION[user_info['function']]).capitalize()}:"),
                             fmt.hlink(f"{user_info['name']}", f"tg://user?id={chat_id}")),
                    fmt.text(fmt.hbold("Действие:"), action),
                    fmt.text(fmt.hbold("Время:"), str(await get_time(tz=api["timezone"]))[:-7]),
                    sep="\n")
    await dp.bot.send_message(chat_id=MODER_LOGS if DEBUG else api["log_chat_id"],
                              text=text, reply_to_message_id=msg_to_reply)
    return


async def reserve_back(tg_id: int, status: str) -> None:
    old_order_status, new_order_status, function_id = await check_first_line_status(status)
    if old_order_status:
        await sql.reset_reserve_status(function_id, [tg_id, old_order_status, new_order_status, None])
    return


async def write_new_status(args: list, location: dict = None, extra_args: list = None) -> None:
    if location:
        args.append(location["latitude"])
        args.append(location["longitude"])
        extra_args = [", $4, $5", ", latitude, longitude"]
    await sql.update_employee_last_status(args, extra_args)
    return
