from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery

from states.fsm import finish_state, get_fsm_data, save_fsm_data
from utils.formate_text import DeliverMenu
from utils.formate_button import DeliverButton, create_reply_markup, return_markup
from utils.status import reserve_back
from utils.message import send_info_log
from utils.db import sql
from utils.proccess_time import get_predict_time_for_delivery
from utils.ozon_express_api.request import start_delivery_api, start_delivery_last_mile, complete_delivery_ozon


deliver_txt = DeliverMenu()
deliver_btn = DeliverButton()


# ****************************************Delivering****************************************
async def get_level_1(function: str, status: str) -> dict:
    return await create_reply_markup(await deliver_txt.menu_1(),
                                     await deliver_btn.buttons_1(function, status))


async def get_level_2(function: str, cll: CallbackQuery) -> dict:
    await reserve_back(cll.from_user.id, "reserve_delivery")
    count = await sql.count_orders(cll.from_user.id, "awaiting_deliver")
    reserved_users = await sql.get_reserved_user(cll.from_user.id, "reserve_delivery")

    return await create_reply_markup(await deliver_txt.menu_2(count, reserved_users),
                                     await deliver_btn.buttons_2(function, count))


async def get_level_3(function: str, cll: CallbackQuery) -> dict:
    callback = cll.data.split(":")
    limit = int(callback[3]) if callback[6] == "ex_add" else None
    orders = await sql.reserve_orders_for_delivery(cll.from_user.id, limit)

    return await create_reply_markup(await deliver_txt.menu_3(len(orders), callback[6]),
                                     await deliver_btn.buttons_3(function, orders, callback[6]))


async def get_level_4(function: str, cll: CallbackQuery) -> dict:
    order = await sql.get_order_info_for_delivering(cll.data.split(":")[5])
    predicted_time = await get_predict_time_for_delivery(order["shipment_date"], 24)

    return await create_reply_markup(await deliver_txt.menu_4(order, predicted_time),
                                     await deliver_btn.buttons_4(function))


async def get_level_5(cll: CallbackQuery) -> dict:
    return await return_markup(await deliver_btn.buttons_5(cll))


async def get_level_6(function: str, cll: CallbackQuery, state: FSMContext, tz: str) -> dict:
    orders = await check_added_orders(cll)
    orders_for_delivery = await sql.start_delivery_order(orders["added"], cll.from_user.id, tz)

    if len(orders_for_delivery) > 0:
        new_orders = await check_new_added_orders(orders_for_delivery, orders["added"])
        await start_delivery_api(cll.from_user.id, new_orders)
        await save_fsm_data(state, data_=[dict(order) for order in orders_for_delivery])
        await reserve_back(cll.from_user.id, "reserve_delivery")
        [await send_info_log(cll.message.chat.id, "Начал доставку", order) for order in new_orders]

    return await create_reply_markup(await deliver_txt.menu_6(len(orders_for_delivery), len(orders["added"])),
                                     await deliver_btn.buttons_6(function, orders_for_delivery))


async def get_level_7(function: str, cll: CallbackQuery, state: FSMContext) -> dict:
    try:
        order = (await get_fsm_data(state, ["data_"]))["data_"][int(cll.data.split(":")[4])]
    except KeyError:
        order = await sql.get_order_info(cll.data.split(":")[5])

    return await create_reply_markup(await deliver_txt.menu_7(order),
                                     await deliver_btn.buttons_7(function))


async def get_level_8(function: str, cll: CallbackQuery, state: FSMContext):
    orders = (await get_fsm_data(state, ["data_"]))["data_"]
    await start_delivery_last_mile(cll.from_user.id, [order["posting_number"] for order in orders])

    return await create_reply_markup(await deliver_txt.menu_8(len(orders)),
                                     await deliver_btn.buttons_8(function, orders))


async def get_level_9(function, tz, cll: CallbackQuery = None, callback=None,
                      reply_markup=None, tg_id=None, location=None):
    callback_ = callback.split(":") if callback else cll.data.split(":")
    markup = reply_markup if reply_markup else cll.message.reply_markup
    current_tg_id = tg_id if tg_id else cll.message.chat.id

    if callback_[6] == "delivered":
        await complete_delivery_ozon(current_tg_id, callback_[5])
        await sql.complete_posting_delivery(callback_[5], current_tg_id, tz, location, 'conditionally_delivered')
        await send_info_log(current_tg_id, "Завершил доставку", callback_[5], "Доставлено")

    elif callback_[6] in ["return", "no_call"]:
        await sql.complete_posting_delivery(callback_[5], current_tg_id, tz, location, 'undelivered')
        await send_info_log(current_tg_id, "Завершил доставку", callback_[5], "Не доставлено",
                            "Отказ" if callback_[6] == "return" else "Не дозвонился")

    buttons, in_process, delivered, undelivered = await deliver_btn.buttons_9(function, callback_, markup)
    return await create_reply_markup(await deliver_txt.menu_9(in_process, delivered, undelivered), buttons)


async def get_level_10(function: str, cll: CallbackQuery):
    await finish_state(cll.message.chat.id, cll.from_user.id)
    option = cll.data.split(":")[4]

    return await create_reply_markup(await deliver_txt.menu_10(option),
                                     await deliver_btn.buttons_10(function, option))


# ****************************************Extra****************************************
async def check_added_orders(cll: CallbackQuery) -> dict:
    added_orders, other_orders = [], []
    if cll.data.split(":")[6] != "ex_reserve_back":
        for ind, button in enumerate(cll.message.reply_markup.inline_keyboard):
            if ind + 1 != len(cll.message.reply_markup.inline_keyboard):
                if button[1].callback_data.split(":")[-1] in ["added", "rem"]:
                    added_orders.append(button[0].text)
                else:
                    other_orders.append(button[0].text)
    return {"added": added_orders, "other": other_orders}


async def check_new_added_orders(added_orders: list, orders: list) -> list:
    new_orders = []
    for order in added_orders:
        if order["posting_number"] in orders:
            new_orders.append(order["posting_number"])
    return new_orders


async def get_callback_data_for_back_button(function: str) -> list:
    return ["main", "1", "0", "0", "0", "back"] if function == 'courier' else ["order", "2", "0", "0", "0", "back"]


async def get_data_level_1(status: str) -> list:
    if status in ["on_shift", "reserve_delivery", "delivering"]:
        return [{"Доставка отправлений": ["delivery", "2", "0", "0", "0", "open"]},
                {"Информация":           ["info", "1", "0", "0", "0", "open"]},
                {"Завершить смену":      ["main", "1", "0", "0", "0", "finish"]}]
    else:
        return [{"Начать смену": ["main", "1", "0", "0", "0", "start"]},
                {"Информация":   ["info", "1", "0", "0", "0", "open"]},
                {"Выйти":        ["main", "0", "0", "0", "0", "close_bot"]}]


async def get_data_level_2(count: int, callback_back: list) -> (str, list):
    if count != 0:
        buttons = [{"Назад":    callback_back,
                    "Доставка": ["delivery", "3", "0", "0", "0", "reserve_delivery"]}]
    else:
        buttons = [{"Назад":    callback_back,
                    "Обновить": ["delivery", "2", "0", "0", "0", "update"]}]
    return buttons


async def get_data_level_3(orders_data: list, action: str) -> (list, int):
    buttons = []
    for ind, order in enumerate(orders_data):
        buttons.append({order["posting_number"]: ["delivery", "4", "0", "0", order["posting_number"], "open"],
                        "☑️":                    ["delivery", "5", "0", "0", order["posting_number"], "add"]})
    if action == "ex_add":
        buttons.append({"Отмена":      ["delivery", "6", "0", "0", "0", "ex_reserve_back"],
                        "Подтвердить": ["delivery", "6", "0", "0", "0", "ex_reserve_delivery"]})
    else:
        buttons.append({"Отмена":      ["delivery", "2", "0", "0", "0", "reserve_back"],
                        "Подтвердить": ["delivery", "6", "0", "0", "0", "reserve_delivery"]})
    return buttons, len(orders_data)


async def get_data_level_6(orders_for_delivery: list) -> (list, list):
    buttons = []
    for ind, order in enumerate(orders_for_delivery):
        buttons.append({order["posting_number"]: ["delivery", "7", "in_process", ind, order["posting_number"], "open"]})
    buttons.append({"Забрал со склада": ["delivery", "8", "0", "0", "0", "open"]})
    if len(orders_for_delivery) <= 4:
        buttons.insert(0, {"Добавить отправления": ["delivery", "3", f"{5 - len(orders_for_delivery)}", "0", "0", "ex_add"]})
    return buttons


async def get_data_level_8(orders: list) -> list:
    buttons = []
    for ind, order in enumerate(orders):
        buttons.append(
            {order["posting_number"]: ["delivery", "7", "in_process", ind, order["posting_number"], "open"]})
        buttons.append(
            {"✖Не доставлен": ["delivery", "9", "button", "0", order["posting_number"], "undelivered"],
             "✔Доставлен": ["delivery", "9", "button", "0", order["posting_number"], "delivered"]})
    return buttons


async def get_data_level_10(consist: str):
    return [{"Вернул заказ на склад" if consist == "undelivered"
             else "Вернулся на склад": ["delivery", "2", "0", "0", "0", "complete"]}]


async def get_data_for_null_orders() -> (list, list):
    buttons = [{"Вернуться": ["main", "1", "0", "0", "0", "back"]}]
    return buttons


if __name__ == '__main__':
    pass
