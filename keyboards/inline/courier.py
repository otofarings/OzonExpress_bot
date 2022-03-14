import aiogram.utils.markdown as fmt
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery

from states.fsm import finish_state, get_fsm_data, save_fsm_data
from utils.geo import get_map_url
from utils.status import send_info_log, reserve_back
from utils.db import sql
from utils.proccess_time import get_predict_time_for_delivery
from utils.ozon_express_api.request import start_delivery_api, start_delivery_last_mile, complete_delivery_ozon
from keyboards.creating import create_inline_keyboard


# ****************************************Delivering****************************************
async def get_level_1(function: str, status: str) -> dict:
    text = [fmt.hbold("Меню доставки 🛺")]

    if status in ["on_shift", "reserve_delivery", "delivering"]:
        buttons = [{"Доставка отправлений": ["delivery", "2", "0", "0", "0", "open"]},
                   {"Информация":           ["main", "1", "0", "0", "0", "pass"]},
                   {"Завершить смену":      ["main", "1", "0", "0", "0", "finish"]}]
    else:
        buttons = [{"Начать смену": ["main", "1", "0", "0", "0", "start"]},
                   {"Информация":   ["main", "1", "0", "0", "0", "pass"]},
                   {"Выйти":        ["main", "0", "0", "0", "0", "close_bot"]}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_2(function: str, cll: CallbackQuery) -> dict:
    text = [fmt.hbold("Меню доставки 🛺\n")]

    await reserve_back(cll.from_user.id, "reserve_delivery")

    count = await sql.count_orders(cll.from_user.id, "awaiting_deliver")
    text.append(fmt.text(fmt.hbold("Доступно:"), count))

    if function == 'courier':
        callback_back = ["main", "1", "0", "0", "0", "back"]
    else:
        callback_back = ["order", "2", "0", "0", "0", "back"]

    if count != 0:
        text.append(fmt.text("\nНажмите", fmt.hbold("Доставка"), ",чтобы перейти к выбору"))
        buttons = [{"Назад":    callback_back,
                    "Доставка": ["delivery", "3", "0", "0", "0", "reserve_delivery"]}]

    else:
        text.append(fmt.text("\nНажмите", fmt.hbold("Обновить"), "через несколько секунд"))
        buttons = [{"Назад":    callback_back,
                    "Обновить": ["delivery", "2", "0", "0", "0", "update"]}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_3(function: str, cll: CallbackQuery) -> dict:
    text = [fmt.hbold("Меню доставки 🛺\n")]

    orders_data = await sql.reserve_orders_for_delivery(cll.from_user.id)

    text.append(fmt.text("Доступно: ", fmt.hbold(len(orders_data))))
    text.append(fmt.text("\nОтметив заказ(ы), нажмите ", fmt.hbold("Подтвердить"), ", чтобы начать доставку"))

    buttons = []
    for ind, order in enumerate(orders_data):
        if ind == 0:
            buttons.append({order["posting_number"]: ["delivery", "4", "0", "0", order["posting_number"], "open"],
                            "✅️":                     ["delivery", "5", "0", "0", order["posting_number"], "added"]})
        else:
            buttons.append({order["posting_number"]: ["delivery", "4", "0", "0", order["posting_number"], "open"],
                            "☑️":                     ["delivery", "5", "0", "0", order["posting_number"], "add"]})

    buttons.append({"Отмена":      ["delivery", "2", "0", "0", "0", "reserve_back"],
                    "Подтвердить": ["delivery", "6", "0", "0", "0", "reserve_delivery"]})

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_4(function: str, cll: CallbackQuery) -> dict:
    text = [fmt.hbold("Меню доставки 🛺\n")]

    callback = cll.data.split(":")

    order = await sql.get_order_info_for_delivering(callback[5])

    complete_time = await get_predict_time_for_delivery(order["shipment_date"], 24)
    text.append(fmt.text(fmt.text(fmt.hbold("Отправление:"), order["posting_number"]),
                         fmt.text(fmt.hbold("Передать клиенту до:"), fmt.text(complete_time)),
                         fmt.text(fmt.hbold("Адрес:"), fmt.hlink(order["address"],
                                                                 await get_map_url(order["latitude"],
                                                                                   order["longitude"]))),
                         sep="\n\n"))

    buttons = [{"Назад": ["delivery", "4", "0", "0", "0", "back"]}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_5(cll: CallbackQuery) -> dict:
    markup = cll.message.reply_markup

    for ind, button in enumerate(markup.inline_keyboard):
        if cll.data == button[1].callback_data:
            new_data = cll.data.split(":")

            if new_data[-1] == "add":
                new_sign, new_data[6] = "✅️", "rem"

            elif new_data[-1] == "rem":
                new_sign, new_data[6] = "☑️️", "add"

            else:
                continue

            markup.inline_keyboard[ind][1].text = new_sign
            markup.inline_keyboard[ind][1].callback_data = ":".join(new_data)

    return {"reply_markup": markup}


async def get_level_6(function: str, cll: CallbackQuery, state: FSMContext, tz: str) -> dict:
    orders = await check_added_orders(cll)
    orders_for_delivery = await sql.start_delivery_order(orders["added"], cll.from_user.id, tz)

    if len(orders_for_delivery) > 0:
        text = [fmt.hbold("Меню доставки 🛺\n"), fmt.text("Необходимо забрать товары со склада")]

        if len(orders_for_delivery) != len(orders["added"]):
            count_cancelled_orders = len(orders["added"]) - len(orders_for_delivery)
            if count_cancelled_orders == 1:
                text.append(fmt.hbold(f"\n❗Статус 1 заказа был изменен, в связи с чем, он не доступен для доставки"))
            else:
                text.append(fmt.hbold(f"\n❗Статусы {count_cancelled_orders} заказов были изменены, в связи с чем, они не доступны для доставки"))

        list_of_orders = [order["posting_number"] for order in orders_for_delivery]

        await start_delivery_api(cll.from_user.id, list_of_orders)
        await send_info_log(cll.message.chat.id, "Начал доставку",
                            fmt.text(fmt.hbold("Отправления:"), fmt.hcode(*list_of_orders)))
        await save_fsm_data(state, data_=[dict(order) for order in orders_for_delivery])

        await reserve_back(cll.from_user.id, "reserve_delivery")

        buttons = []
        for ind, order in enumerate(orders_for_delivery):
            buttons.append({order["posting_number"]: ["delivery", "7", "in_process",
                                                      ind, order["posting_number"], "open"]})
        buttons.append({"Забрал со склада": ["delivery", "8", "0", "0", "0", "open"]})

    else:
        text = [fmt.hbold("Меню доставки 🛺\n"),
                fmt.text("Выбранный заказ был отменен❗\n\nДля продолжения нажмите", fmt.hbold("Вернуться"))]

        buttons = [{"Вернуться": ["main", "1", "0", "0", "0", "back"]}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_7(function: str, cll: CallbackQuery, state: FSMContext) -> dict:
    text = [fmt.hbold("Меню доставки 🛺\n")]

    orders = (await get_fsm_data(state, ["data_"]))["data_"]
    callback = cll.data.split(":")

    text.append(fmt.text(fmt.text(fmt.hbold("\nОтправление:"), orders[int(callback[4])]["posting_number"]),
                         fmt.text(fmt.hbold("Передать клиенту до:"), str(orders[int(callback[4])]["shipment_date"])),
                         fmt.text(fmt.hbold("\nАдрес:"), fmt.hlink(orders[int(callback[4])]["address"],
                                                                   await get_map_url(
                                                                       orders[int(callback[4])]["latitude"],
                                                                       orders[int(callback[4])]["longitude"]))),
                         fmt.text(fmt.hbold("\nПолучатель:"), (orders[int(callback[4])]['addressee_name'])),
                         fmt.text(fmt.hbold("Телефон:"), fmt.hcode(f"+{orders[int(callback[4])]['addressee_phone']}")),
                         fmt.text(fmt.hbold("\nКоментарий:"), orders[int(callback[4])]['customer_comment']),
                         sep='\n'))

    buttons = [{"Назад": ["delivery", "7", "0", "0", "0", "back"]}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_8(function: str, cll: CallbackQuery, state: FSMContext):
    text = [fmt.hbold("Меню доставки 🛺\n")]

    orders = (await get_fsm_data(state, ["data_"]))["data_"]

    await start_delivery_last_mile(cll.from_user.id, [order["posting_number"] for order in orders])

    text.append(fmt.text(fmt.text(fmt.hbold("Прогресс: "), fmt.hbold("0"),
                                  " из ", fmt.hbold(f"{len(orders)}")),
                         sep="\n"))

    buttons = []
    for ind, order in enumerate(orders):
        buttons.append(
            {order["posting_number"]: ["delivery", "7", "in_process", ind, order["posting_number"], "open"]})
        buttons.append(
            {"✖Не доставлен":         ["delivery", "9", "button", "0", order["posting_number"], "undelivered"],
             "✔Доставлен":            ["delivery", "9", "button", "0", order["posting_number"], "delivered"]})

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_9(function, tz, cll: CallbackQuery = None, callback=None,
                      reply_markup=None, tg_id=None, location=None):
    text = [fmt.hbold("Меню доставки 🛺\n")]

    callback_ = callback.split(":") if callback else cll.data.split(":")
    current_reply_markup = reply_markup if reply_markup else cll.message.reply_markup
    current_tg_id = tg_id if tg_id else cll.message.chat.id
    in_process, delivered, undelivered = 0, 0, 0

    buttons = []
    for row in current_reply_markup.inline_keyboard:
        if len(row) == 1:
            for button in row:
                button_data = button.callback_data.split(":")

                if callback_[5] == button_data[5]:
                    if callback_[6] == "undelivered":
                        buttons.append(
                            {f"{button.text}": ["delivery", "7", "cancel", button_data[4], button_data[5], "open"]})
                        buttons.append(
                            {"Назад": ["delivery", "9", "button", button_data[4], button_data[5], "back"],
                             "🔙Отказ от товара": ["delivery", "9", "button", button_data[4], button_data[5], "return"],
                             "📵Не дозвонился":   ["delivery", "9", "button", button_data[4], button_data[5], "no_call"]})

                        in_process += 1

                    elif callback_[6] == "delivered":
                        await complete_delivery_ozon(current_tg_id, button.text)
                        await sql.complete_posting_delivery(button_data[5], current_tg_id,
                                                            tz, location, 'conditionally_delivered')
                        await send_info_log(current_tg_id, "Завершил доставку",
                                            fmt.text(fmt.text(fmt.hbold("Отправление:"), button.text),
                                                     fmt.text(fmt.hbold("Статус:"), "Доставлено"),
                                                     sep="\n"))

                        buttons.append(
                            {f"{button.text} ✅": ["delivery", "7", "delivered", button_data[4], button_data[5], "open"]})

                        delivered += 1

                    elif callback_[6] in ["return", "no_call"]:

                        await sql.complete_posting_delivery(button_data[5], current_tg_id, tz, location, 'undelivered')
                        await send_info_log(current_tg_id, "Завершил доставку",
                                            fmt.text(fmt.text(fmt.hbold("Отправление:"), button.text),
                                                     fmt.text(fmt.hbold("Статус:"), "Не доставлено"),
                                                     fmt.text(fmt.hbold("Причина:"),
                                                              "Отказ" if callback_[6] == "return" else "Не дозвонился"),
                                                     sep="\n"))

                        posting_button = f"{button.text} 📵" if callback_[6] == "no_call" else f"{button.text} 🔙"
                        buttons.append(
                            {posting_button: ["delivery", "7", "undelivered", button_data[4], button_data[5], "open"]})

                        undelivered += 1

                    elif callback_[6] in ["back"]:
                        buttons.append({
                            button.text: ["delivery", "7", "in_process", button_data[4], button_data[5], "open"]})
                        buttons.append({
                            "✖Не доставлен": ["delivery", "9", "button", button_data[4], button_data[5], "undelivered"],
                            "✔Доставлен": ["delivery", "9", "button", button_data[4], button_data[5], "delivered"]})
                        in_process += 1

                elif button_data[3] == "in_process":
                    buttons.append({
                        button.text:     ["delivery", "7", "in_process", button_data[4], button_data[5], "open"]})
                    buttons.append({
                        "✖Не доставлен": ["delivery", "9", "button", button_data[4], button_data[5], "undelivered"],
                        "✔Доставлен":    ["delivery", "9", "button", button_data[4], button_data[5], "delivered"]})
                    in_process += 1

                elif button_data[3] == "cancel":
                    buttons.append({
                        button.text:         ["delivery", "7", "cancel", button_data[4], button_data[5], "open"]})
                    buttons.append({
                        "Назад":             ["delivery", "9", "button", button_data[4], button_data[5], "back"],
                        "🔙Отказ от товара": ["delivery", "9", "button", button_data[4], button_data[5], "return"],
                        "📵Не дозвонился":   ["delivery", "9", "button", button_data[4], button_data[5], "no_call"]})
                    in_process += 1

                elif button_data[3] == "delivered":
                    buttons.append({
                        button.text: ["delivery", "7", "delivered", button_data[4], button_data[5], "open"]})
                    delivered += 1

                elif button_data[3] == "undelivered":
                    buttons.append({
                        button.text: ["delivery", "7", "undelivered", button_data[4], button_data[5], "open"]})
                    undelivered += 1

                break

    total_count = in_process + delivered + undelivered
    text.append(fmt.text(fmt.text(fmt.hbold("Прогресс:"), fmt.hbold(total_count - in_process),
                                  " из ", fmt.hbold(total_count)),
                         sep="\n"))

    if in_process == 0:
        if undelivered == 0:
            text.append(fmt.text("\nОтлично! Вы доставили все заказы\n"))
            buttons.append({"Возвращаюсь на склад": ["delivery", "10", "returning", "0", "0", "open"]})

        else:
            text.append(fmt.text(fmt.text("\nВы завершили доставку"),
                                 fmt.text("Не забудьте вернуть недоставленный товар на склад"),
                                 sep="\n"))
            buttons.append({"Возвращаюсь на склад": ["delivery", "10", "returning", "undelivered", "0", "open"]})

        text.append(fmt.text("\nНажмите кнопку", fmt.hbold("Возвращаюсь на склад"), ", чтобы завершить доставку"))

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_10(function: str, cll: CallbackQuery):
    text = [fmt.hbold("Меню доставки 🛺\n")]

    await finish_state(cll.message.chat.id, cll.from_user.id)

    if cll.data.split(":")[-3] == "undelivered":
        text.append(fmt.text(fmt.text("После передачи товара на склад, нажмите кнопку ниже, для выхода в главное меню"),
                             sep="\n"))

        buttons = [{"Вернул заказ на склад": ["delivery", "2", "0", "0", "0", "complete"]}]

    else:
        text.append(fmt.text(fmt.text("\nДля выхода в главное меню, нажмите кнопку ниже"),
                             sep="\n"))

        buttons = [{"Вернулся на склад": ["delivery", "2", "0", "0", "0", "complete"]}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def check_added_orders(cll: CallbackQuery) -> dict:
    added_orders, other_orders = [], []
    for ind, button in enumerate(cll.message.reply_markup.inline_keyboard):
        if ind + 1 != len(cll.message.reply_markup.inline_keyboard):
            if button[1].callback_data.split(":")[-1] in ["added", "rem"]:
                added_orders.append(button[0].text)

            else:
                other_orders.append(button[0].text)

    return {"added": added_orders, "other": other_orders}
