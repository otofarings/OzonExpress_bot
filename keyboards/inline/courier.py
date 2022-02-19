import aiogram.utils.markdown as fmt
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData

from loader import dp
from data.config import MODER_LOGS, DEBUG
from states.fsm import finish_state
from utils.db_api import extra, orders
from utils.db_api.database import db_query
from utils.proccess_time import get_time
from utils.ozon_express_api.request import start_delivery, start_delivery_last_mile, complete_delivery_ozon

callback_data = CallbackData("courier", "menu", "level", "option", "item", "item_id", "action")

menu_name = fmt.hbold("Меню доставки заказов")


async def create_button(text: str, args: list):
    return InlineKeyboardButton(text=text, callback_data=callback_data.new(*args))


async def check_action_menu(chat_id, action, status, tz, location=None):
    new_status = status

    if action == "back":
        await db_query(func='fetch',
                       sql="""WITH updated AS (UPDATE order_info 
                                               SET status = $3, deliver_id = $4
                                               WHERE status = $2 AND deliver_id = $1 
                                               RETURNING *)
                              SELECT count(posting_number) 
                              FROM updated 
                              WHERE status = $3 AND warehouse_id IN (SELECT warehouse_id 
                                                                     FROM employee 
                                                                     WHERE tg_id = $1);""",
                       kwargs=[chat_id, 'reserved_by_deliver', 'awaiting_deliver', None])

    elif action == "complete":
        await send_info_log(chat_id, "Вернулся на склад")
        new_status = 'на смене'

    elif (status == 'не на смене') and (action == "start"):
        await send_info_log(chat_id, "Начал смену")
        new_status = 'на смене'

    elif action == "finish":
        await send_info_log(chat_id, "Завершил смену")
        new_status = 'не на смене'

    if status != new_status:
        if action in ["start", "finish"]:
            await db_query(func='execute',
                           sql="""WITH updated AS (UPDATE employee 
                                                   SET status = $2 
                                                   WHERE tg_id = $1 
                                                   RETURNING *)
                                  INSERT INTO logs_status_changes 
                                  (employee_id, status, date, latitude, longitude) 
                                  VALUES($1, $2, $3, $4, $5);""",
                           kwargs=[chat_id, new_status, await get_time(tz=tz),
                                   location["latitude"], location["longitude"]])
        else:
            await db_query(func='execute',
                           sql="""WITH updated AS (UPDATE employee 
                                                   SET status = $2 
                                                   WHERE tg_id = $1 
                                                   RETURNING *)
                                  INSERT INTO logs_status_changes 
                                  (employee_id, status, date) 
                                  VALUES($1, $2, $3);""",
                           kwargs=[chat_id, new_status, await get_time(tz=tz)])
    return new_status


async def send_info_log(chat_id: int, action: str, ex_option=None):
    api = await db_query(func='fetch',
                         sql="""SELECT * 
                                FROM api 
                                WHERE seller_id = (SELECT seller_id 
                                                   FROM employee 
                                                   WHERE tg_id = $1);""",
                         kwargs=[chat_id])

    user_info = await db_query(func='fetch',
                               sql="""SELECT * 
                                      FROM employee 
                                      WHERE tg_id = $1;""",
                               kwargs=[chat_id])

    await dp.bot.send_message(chat_id=MODER_LOGS if DEBUG else api[0][0]["log_chat_id"],
                              text=fmt.text(ex_option if ex_option else '',
                                            fmt.text(fmt.hbold("Курьер: "),
                                                     fmt.hlink(f"{user_info[0][0]['name']}",
                                                               f"tg://user?id={chat_id}")),
                                            fmt.text(fmt.hbold("Действие: "), action),
                                            fmt.text(fmt.hbold("Время: "),
                                                     str(await get_time(tz=api[0][0]["timezone"]))[:-7]),
                                            sep="\n"))
    return


async def check_location():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add(KeyboardButton("Назад"), KeyboardButton("Мое местоположение", request_location=True))

    return {'text': 'Для продолжения предоставьте местоположение, нажав кнопку ниже', 'reply_markup': markup}


# ****************************************Main****************************************
async def get_main_menu(status):
    """
    Menu: main
    Level: 1
    """
    markup = InlineKeyboardMarkup()

    if status in ['на смене', 'доставляет']:
        markup.row(await create_button("Доставка отправлений", ["order", "2", "0", "0", "0", "open"]))
        markup.row(await create_button("Информация", ["main", "1", "0", "0", "0", "pass"]))
        markup.row(await create_button("Завершить смену", ["main", "1", "0", "0", "0", "finish"]))
    else:
        markup.row(await create_button("Начать смену", ["main", "1", "0", "0", "0", "start"]))
        markup.row(await create_button("Информация", ["main", "1", "0", "0", "0", "pass"]))
        markup.row(await create_button("Выйти", ["main", "0", "0", "0", "0", "close"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name)}


# ****************************************Orders****************************************
async def open_start_menu(cll: CallbackQuery):
    """
    Menu: order
    Level: 2
    """
    markup = InlineKeyboardMarkup()

    count = await db_query(func='fetch',
                           sql="""SELECT count(posting_number) 
                                  FROM order_info 
                                  WHERE status = $2 AND warehouse_id IN (SELECT warehouse_id 
                                                                         FROM employee 
                                                                         WHERE tg_id = $1);""",
                           kwargs=[cll.from_user.id, 'awaiting_deliver'])

    orders_info = fmt.text("Доступно заказов:", fmt.hbold(count[0][0]["count"]))

    if count[0][0]["count"] != 0:
        info_text = fmt.text("\nНажмите ", fmt.hbold("Взять заказ"), " ,чтобы перейти к выбору")
        markup.row(await create_button("Назад", ['main', "1", "0", "0", "0", "open"]),
                   await create_button("Взять заказ", ["order", "3", "0", "0", "0", "open"]))

    else:
        info_text = fmt.text("\nНажмите ", fmt.hbold("Обновить"), "через несколько секунд")
        markup.row(await create_button("Назад", ["main", "1", "0", "0", "0", "open"]),
                   await create_button("Обновить", ["order", "2", "0", "0", "0", "update"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, orders_info, info_text, sep="\n")}


async def get_order_menu(tg_id: int):
    """
    Menu: Orders management (Orders list)
    Level: 3
    """
    markup = InlineKeyboardMarkup()

    orders_data = await db_query(func='fetch',
                                 sql="""SELECT posting_number, latitude, longitude 
                                        FROM order_info 
                                        WHERE status = $2 AND warehouse_id IN (SELECT warehouse_id 
                                                                               FROM employee 
                                                                               WHERE tg_id = $1)
                                        ORDER BY shipment_date;""",
                                 kwargs=[tg_id, 'awaiting_deliver'])
    # Заменить
    sorted_orders = await orders.get_similar_orders(orders_data[0][0], orders_data[0])

    final_orders = await db_query(func='fetch',
                                  sql="""WITH updated AS (UPDATE order_info 
                                                          SET status = $3, deliver_id = $2 
                                                          WHERE posting_number = ANY($1) 
                                                          RETURNING *)
                                         SELECT posting_number, address, shipment_date 
                                         FROM updated 
                                         WHERE status = $3 AND warehouse_id IN (SELECT warehouse_id 
                                                                                FROM employee 
                                                                                WHERE tg_id = $2)
                                         ORDER BY shipment_date;""",
                                  kwargs=[tuple([order['posting_number'] for order in sorted_orders]),
                                          tg_id, 'reserved_by_deliver'])

    orders_data = final_orders[0]

    orders_info = fmt.text("Доступно заказов: ", fmt.hbold(len(orders_data)))
    info_text = fmt.text("\nОтметив заказ(ы), нажмите ", fmt.hbold("Подтвердить"), ", чтобы начать доставку")

    for ind, order in enumerate(orders_data):
        if ind == 0:
            markup.row(await create_button(order["posting_number"], ["order", "4", "0", "0",
                                                                     order["posting_number"], "open"]),
                       await create_button("✅️", ["order", "4", "0", "0", order["posting_number"], "added"]))
        else:
            markup.row(await create_button(order["posting_number"], ["order", "4", "0", "0",
                                                                     order["posting_number"], "open"]),
                       await create_button("☑️️", ["order", "4", "0", "0", order["posting_number"], "add"]))

    markup.row(await create_button("Отмена", ["order", "2", "0", "0", "0", "back"]),
               await create_button("Подтвердить", ["order", "5", "0", "0", "0", "open"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, orders_info, info_text, sep="\n")}


async def get_order_info_menu(cll: CallbackQuery = None, state=None):
    """
    Menu: Orders management (Orders list)
    Level: 4
    """
    if cll:
        await extra.save_previous(cll.message.html_text, cll.message.reply_markup, state, first=True)

        markup = InlineKeyboardMarkup()

        order = await db_query(func='fetch',
                               sql="""SELECT posting_number, address, shipment_date, latitude, longitude
                                      FROM order_info 
                                      WHERE posting_number = $1 AND status = $2;""",
                               kwargs=[cll.data.split(":")[-2], 'reserved_by_deliver'])
        order = order[0][0]
        orders_info = fmt.text(fmt.text(fmt.hbold("\nНомер отправления: "), fmt.text(order["posting_number"])),
                               fmt.text(fmt.hbold("Время доставки: "), fmt.text(order["shipment_date"])),
                               fmt.text(fmt.hbold("\nАдрес: "), fmt.hlink(order["address"],
                                                                          await extra.get_map_url(order["latitude"],
                                                                                                  order["longitude"]))),
                               sep="\n")

        markup.row(await create_button("Назад", ["order", "4", "0", "0", "0", "back"]))

        return {"reply_markup": markup, "text": fmt.text(menu_name, orders_info, sep="\n")}

    else:
        return await extra.save_previous(state=state, get=True, last=True, menu=True)


async def get_order_select_menu(cll: CallbackQuery):
    """
    Menu: Orders management (Orders list)
    Level: 4
    """
    markup = cll.message.reply_markup

    for ind, button in enumerate(markup.inline_keyboard):
        if cll.data == button[1].callback_data:
            new_data = cll.data.split(":")

            if new_data[-1] == "add":
                new_sign, new_data[-1] = "✅️", "rem"

            elif new_data[-1] == "rem":
                new_sign, new_data[-1] = "☑️️", "add"

            else:
                continue

            markup.inline_keyboard[ind][1].text = new_sign
            markup.inline_keyboard[ind][1].callback_data = ":".join(new_data)

    return {"reply_markup": markup}


async def get_delivering_menu(cll: CallbackQuery, state, tz):
    """
    Menu: Orders management (Orders list)
    Level: 5
    """
    markup = InlineKeyboardMarkup()
    info_text = fmt.text(fmt.text(fmt.hbold("Статус: "), "получение"),
                         fmt.text("Необходимо забрать товары со склада"),
                         sep="\n\n")

    added_orders, other_orders = [], []
    for ind, button in enumerate(cll.message.reply_markup.inline_keyboard):
        if ind + 1 != len(markup.inline_keyboard):
            if button[1].callback_data.split(":")[-1] in ["added", "rem"]:
                added_orders.append(button[0].text)

            else:
                other_orders.append(button[0].text)

    orders_for_delivery = await db_query(func='fetch',
                                         sql="""WITH updated AS (UPDATE order_info 
                                                                 SET status = $3, start_delivery_date = $4 
                                                                 WHERE posting_number = ANY($1) AND deliver_id = $2 
                                                                 RETURNING *)
                                                SELECT order_id, posting_number, address, addressee_name, 
                                                       addressee_phone, customer_comment, shipment_date, 
                                                       latitude, longitude
                                                FROM updated 
                                                WHERE status = $3 AND warehouse_id IN (SELECT warehouse_id 
                                                                                       FROM employee 
                                                                                       WHERE tg_id = $2);""",
                                         kwargs=[tuple(added_orders), cll.from_user.id, 'delivering',
                                                 (await get_time(tz=tz)).replace(tzinfo=None)])

    list_of_orders = [order["posting_number"] for order in orders_for_delivery[0]]
    await start_delivery(cll.from_user.id, list_of_orders)
    await send_info_log(cll.message.chat.id, "Начал доставку",
                        fmt.text(fmt.hbold("Номера отправлений: "), fmt.hcode(*list_of_orders)))

    await extra.save_previous(data_new=[dict(order) for order in orders_for_delivery[0]], first=True, state=state)

    if other_orders:
        await db_query(func='fetch',
                       sql="""WITH updated AS (UPDATE order_info 
                                               SET status = $3, deliver_id = $4 
                                               WHERE status = $2 AND deliver_id = $1 
                                               RETURNING *)
                              SELECT count(posting_number) 
                              FROM updated 
                              WHERE status = $3 AND warehouse_id IN (SELECT warehouse_id 
                                                                     FROM employee 
                                                                     WHERE tg_id = $1);""",
                       kwargs=[cll.from_user.id, 'reserved_by_deliver', 'awaiting_deliver', None])

    for ind, order in enumerate(orders_for_delivery[0]):
        markup.row(await create_button(order["posting_number"],
                                       ["order", "6", "in_process", ind, order["posting_number"], "open"]))

    markup.row(await create_button("Забрал со склада", ["order", "7", "0", "0", "0", "open"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, info_text, sep="\n")}


async def get_delivering_order_info(cll: CallbackQuery = None, state=None):
    """
    Menu: Orders management (Orders list)
    Level: 6
    """
    if cll:
        markup = InlineKeyboardMarkup()

        await extra.save_previous(cll.message.html_text, cll.message.reply_markup, state=state)
        order, option = await extra.save_previous(state=state, get=True), cll.data.split(":")

        orders_info = fmt.text(fmt.text(fmt.hbold("\nНомер отправления: "),
                                        fmt.text(order[int(option[4])]["posting_number"])),
                               fmt.text(fmt.hbold("Время доставки: "),
                                        str(order[int(option[4])]["shipment_date"])),
                               fmt.text(fmt.hbold("\nАдрес: "), fmt.hlink(order[int(option[4])]["address"],
                                                                          await extra.get_map_url(
                                                                              order[int(option[4])]["latitude"],
                                                                              order[int(option[4])]["longitude"]))),
                               fmt.text(fmt.hbold("\nПолучатель: "), (order[int(option[4])]['addressee_name'])),
                               fmt.text(fmt.hbold("Телефон: "),
                                        fmt.hcode(f"+{order[int(option[4])]['addressee_phone']}")),
                               fmt.text(fmt.hbold("\nКоментарий: "), order[int(option[4])]['customer_comment']),
                               sep='\n')

        markup.row(await create_button("Назад", ["order", "6", "0", "0", "0", "back"]))

        return {"reply_markup": markup, "text": fmt.text(menu_name, orders_info, sep="\n")}

    else:
        return await extra.save_previous(state=state, get=True, menu=True)


async def get_delivering_menu_next(cll: CallbackQuery, state, tz):
    """
    Menu: Orders management (Orders list)
    Level: 7
    """
    markup = InlineKeyboardMarkup()

    orders_for_delivery = await extra.save_previous(state=state, get=True)

    list_of_orders = [order["posting_number"] for order in orders_for_delivery]
    await start_delivery_last_mile(cll.from_user.id, list_of_orders)

    info_text = fmt.text(fmt.text(fmt.hbold("Статус: "), "в процессе"),
                         fmt.text(fmt.hbold("Прогресс: "), fmt.hbold("0"),
                                  " из ", fmt.hbold(f"{len(orders_for_delivery)}")),
                         sep="\n")

    for ind, order in enumerate(orders_for_delivery):
        markup.row(await create_button(order["posting_number"], ["order", "6", "in_process", ind,
                                                                 order["posting_number"], "open"]))
        markup.row(await create_button("✖Не доставлен", ["order", "7", "button", "0",
                                                         order["posting_number"], "undelivered"]),
                   await create_button("✔Доставлен", ["order", "7", "button", "0",
                                                      order["posting_number"], "delivered"]))

    await db_query(func='execute',
                   sql="""WITH updated AS (UPDATE employee 
                                           SET status = $2 
                                           WHERE tg_id = $1 
                                           RETURNING *)
                          INSERT INTO logs_status_changes 
                          (employee_id, status, date) 
                          VALUES($1, $2, $3);""",
                   kwargs=[cll.message.chat.id, 'доставляет', await get_time(tz=tz)])

    return {"reply_markup": markup, "text": fmt.text(menu_name, info_text, sep="\n")}


async def get_result_delivering_menu(tz, cll: CallbackQuery = None,
                                     callback=None, reply_markup=None, tg_id=None, location=None):
    """
    Menu: Orders management (Orders list)
    Level: 7
    """

    markup = InlineKeyboardMarkup()

    current_callback = callback if callback else cll.data
    current_reply_markup = reply_markup if reply_markup else cll.message.reply_markup
    current_tg_id = tg_id if tg_id else cll.message.chat.id
    callback, in_process, delivered, undelivered = current_callback.split(":"), 0, 0, 0

    print(current_reply_markup)
    for row in current_reply_markup.inline_keyboard:
        print(row)
        if len(row) == 1:
            for button in row:
                print(button)
                button_data = button.callback_data.split(":")

                if callback[-2] == button_data[-2]:
                    if callback[-1] == "undelivered":
                        markup.row(await create_button(f"{button.text} 😔",
                                                       ["order", "6", "cancel", button_data[-3],
                                                        button_data[-2], "open"]))

                        markup.row(await create_button(f"🔙Отказ от товара",
                                                       ["order", "7", "button", button_data[-3],
                                                        button_data[-2], "return"]),
                                   await create_button(f"📵Не дозвонился",
                                                       ["order", "7", "button", button_data[-3],
                                                        button_data[-2], "no_call"]))
                        in_process += 1

                    elif callback[-1] == "delivered":
                        await complete_delivery_ozon(current_tg_id, button.text)

                        markup.row(await create_button(f"{button.text} 😁",
                                                       ["order", "6", "delivered", button_data[-3],
                                                        button_data[-2], "open"]))

                        await db_query(func='execute',
                                       sql="""WITH updated AS (UPDATE order_info 
                                                               SET status = $2, finish_delivery_date = $3,
                                                                   finish_delivery_latitude = $6, 
                                                                   finish_delivery_longitude = $7
                                                               WHERE posting_number = $1 
                                                               RETURNING *)
                                              INSERT INTO logs_status_changes
                                              (posting_number, status_ozon_seller, date, 
                                               status, employee_id, latitude, longitude)
                                              VALUES($1, $2, $3, $4, $5, $6, $7);""",
                                       kwargs=[button_data[-2], 'delivering',
                                               (await get_time(tz=tz)).replace(tzinfo=None), 'delivered',
                                               current_tg_id, location['latitude'], location['longitude']])

                        await send_info_log(current_tg_id, "Завершил заказ",
                                            fmt.text(fmt.text(fmt.hbold("Номер отправления: "), button.text),
                                                     fmt.text(fmt.hbold("Статус: "), "Доставлено"),
                                                     sep="\n"))
                        delivered += 1

                    elif callback[-1] in ["return", "no_call"]:
                        markup.row(await create_button(
                            f"{button.text} 📵" if callback[-1] == "no_call" else f"{button.text} 🔙",
                            ["order", "6", "undelivered", button_data[-3], button_data[-2], "open"]))
                        reason = "Отказ" if callback[-1] == "return" else "Не дозвонился"

                        await db_query(func='execute',
                                       sql="""WITH updated AS (UPDATE order_info 
                                                               SET status = $2, finish_delivery_date = $3,
                                                                   finish_delivery_latitude = $6, 
                                                                   finish_delivery_longitude = $7
                                                               WHERE posting_number = $1 
                                                               RETURNING *)
                                              INSERT INTO logs_status_changes
                                              (posting_number, status_ozon_seller, date, 
                                               status, employee_id, latitude, longitude)
                                              VALUES($1, $2, $3, $4, $5, $6, $7);""",
                                       kwargs=[button_data[-2], 'delivering',
                                               (await get_time(tz=tz)).replace(tzinfo=None), 'undelivered',
                                               current_tg_id, location['latitude'], location['longitude']])

                        await send_info_log(current_tg_id, "Завершил заказ",
                                            fmt.text(fmt.text(fmt.hbold("Номер отправления: "), button.text[:-1]),
                                                     fmt.text(fmt.hbold("Статус: "), "Не доставлено"),
                                                     fmt.text(fmt.hbold("Причина: "), reason),
                                                     sep="\n"))
                        undelivered += 1

                elif button_data[3] == "in_process":
                    markup.row(await create_button(button.text,
                                                   ["order", "6", "in_process", button_data[-3],
                                                    button_data[-2], "open"]))
                    markup.row(await create_button("✖Не доставлен", ["order", "7", "button", button_data[-3],
                                                                     button_data[-2], "undelivered"]),
                               await create_button("✔Доставлен", ["order", "7", "button", button_data[-3],
                                                                  button_data[-2], "delivered"]))
                    in_process += 1

                elif button_data[3] == "cancel":
                    markup.row(await create_button(button.text, ["order", "6", "cancel", button_data[-3],
                                                                 button_data[-2], "open"]))
                    markup.row(
                        await create_button(f"🔙Отказ от товара",
                                            ["order", "7", "button", button_data[-3], button_data[-2], "return"]),
                        await create_button(f"📵Не дозвонился",
                                            ["order", "7", "button", button_data[-3], button_data[-2], "no_call"]))
                    in_process += 1

                elif button_data[3] == "delivered":
                    markup.row(await create_button(button.text, ["order", "6", "delivered", button_data[-3],
                                                                 button_data[-2], "open"]))
                    delivered += 1

                elif button_data[3] == "undelivered":
                    markup.row(await create_button(button.text, ["order", "6", "undelivered", button_data[-3],
                                                                 button_data[-2], "open"]))
                    undelivered += 1

                break

    if in_process == 0:
        if undelivered == 0:
            final_msg = fmt.text("\nОтлично! Вы доставили все заказы🥳\n")
            markup.row(await create_button("Возвращаюсь на склад", ["order", "8", "returning", "0", "0", "open"]))

        else:
            final_msg = fmt.text(fmt.text("\nВы завершили доставку🙂\n"),
                                 fmt.text("Не забудьте вернуть недоставленный товар на склад😉\n"))
            markup.row(await create_button("Возвращаюсь на склад",
                                           ["order", "8", "returning", "undelivered", "0", "open"]))

        final_info_text = fmt.text("Нажмите кнопку ", fmt.hbold("Возвращаюсь на склад"), ", чтобы завершить доставку")
        status = "завершено"
    else:
        final_msg, final_info_text, status = fmt.text(""), fmt.text(""), "доставка"

    total_count = in_process + delivered + undelivered
    info_text = fmt.text(fmt.text(fmt.hbold("Статус: "), status),
                         fmt.text(fmt.hbold("Прогресс: "), fmt.hbold(total_count - in_process),
                                  " из ", fmt.hbold(total_count)),
                         sep="\n")

    return {"reply_markup": markup, "text": fmt.text(menu_name, info_text, final_msg, final_info_text, sep="\n")}


async def get_complete_delivery_menu(cll: CallbackQuery):
    """
    Menu: Orders management (Orders list)
    Level: 8
    """
    markup = InlineKeyboardMarkup()

    await finish_state(cll.message.chat.id, cll.from_user.id)

    if cll.data.split(":")[-3] == "undelivered":
        info_text = fmt.text(fmt.text(fmt.hbold("Статус: "), "Завершено"),
                             fmt.text("После передачи товара на склад, нажмите кнопку ниже, для выхода в главное меню"),
                             sep="\n")

        markup.row(await create_button("Вернул заказ на склад", ["order", "2", "0", "0", "0", "complete"]))
    else:
        info_text = fmt.text(fmt.text(fmt.hbold("Статус: "), "Завершено"),
                             fmt.text("\nДля выхода в главное меню, нажмите кнопку ниже"),
                             sep="\n")

        markup.row(await create_button("Вернулся на склад", ["order", "2", "0", "0", "0", "complete"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, info_text, sep="\n")}
