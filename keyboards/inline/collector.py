from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData
import aiogram.utils.markdown as fmt

from loader import dp
from data.config import MODER_LOGS, DEBUG
from data.condition import CANCELLATION_STATUS
from states.fsm import finish_state
from utils.db_api import extra
from utils.db_api.message import push_info_msg
from utils.db_api.database import db_query
from utils.ozon_express_api import request
from utils.proccess_time import get_time

callback_data = CallbackData("collector", "menu", "level", "option", "item", "item_id", "action")

menu_name = fmt.hbold("Меню сборки")


async def check_action_menu(chat_id, action, status, tz, error_id=None, posting_number=None, location=None):
    new_status = status

    if action == "back":
        await db_query(func='execute',
                       sql="""UPDATE order_info 
                              SET status = $3, packer_id = $4 
                              WHERE status = $2 AND packer_id = $1;""",
                       kwargs=[chat_id, 'reserved_by_packer', 'awaiting_packaging', None])
    elif (status == 'не на смене') and (action == "start"):
        await send_info_log(chat_id, "Начал смену")
        new_status = 'на смене'

    elif action == "finish":
        await send_info_log(chat_id, "Завершил смену")
        new_status = 'не на смене'

    elif action == "complete":
        await send_info_log(chat_id, "Вернулся на склад")
        new_status = 'на смене'

    elif action == "cancel":
        if error_id == "402":
            pass
        else:
            await db_query(func="execute",
                           sql="cancel_packaging",
                           kwargs=[posting_number, "canceled", (await get_time(tz=tz)).replace(tzinfo=None),
                                   "canceled", int(posting_number), CANCELLATION_STATUS[int(error_id)],
                                   "seller", "Продавец"])

            await send_info_log(chat_id, "Отменил заказ", fmt.text(fmt.hbold("Заказ: "), fmt.hcode(posting_number)))
            await push_info_msg(chat_id, "Заказ отменен!")

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


async def create_button(text: str, args: list):
    return InlineKeyboardButton(text=text, callback_data=callback_data.new(*args))


async def send_info_log(chat_id: int, action: str, ex_option=None):
    api = await db_query(func='fetch',
                         sql="""SELECT * FROM api WHERE seller_id = (SELECT seller_id FROM employee 
                                                                             WHERE tg_id = $1);""",
                         kwargs=[chat_id])
    user_info = await db_query(func='fetch',
                               sql="""SELECT * FROM employee WHERE tg_id = $1;""",
                               kwargs=[chat_id])

    await dp.bot.send_message(chat_id=MODER_LOGS if DEBUG else api[0][0]["log_chat_id"],
                              text=fmt.text(ex_option if ex_option else "",
                                            fmt.text(fmt.hbold("Сборщик: "),
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
    markup = InlineKeyboardMarkup()

    if status in ['на смене', 'собирает']:
        markup.row(await create_button("Сборка отправлений", ["order", "2", "0", "0", "0", "open"]))
        markup.row(await create_button("Информация", ["main", "1", "0", "0", "0", "pass"]))
        markup.row(await create_button("Завершить смену", ["main", "1", "0", "0", "0", "finish"]))
    else:
        markup.row(await create_button("Начать смену", ["main", "1", "0", "0", "0", "start"]))
        markup.row(await create_button("Информация", ["main", "1", "0", "0", "0", "pass"]))
        markup.row(await create_button("Выйти", ["main", "0", "0", "0", "0", "close"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name)}


# ****************************************Orders****************************************
async def open_start_menu(cll: CallbackQuery, tz: str):
    markup = InlineKeyboardMarkup()

    await check_action_menu(cll.data.split(":"), cll, dp, tz)

    count = await db_query(func='fetch',
                           sql="""SELECT count(posting_number) FROM order_info 
                                          WHERE status = $2 AND warehouse_id IN (SELECT warehouse_id FROM employee 
                                                                                 WHERE tg_id = $1);""",
                           kwargs=[cll.from_user.id, "awaiting_packaging"])
    orders_info = fmt.text("Доступно заказов: ", fmt.hbold(count[0][0]["count"]))

    if count[0][0]["count"] != 0:
        info_text = fmt.text("\nНажмите ", fmt.hbold("Собрать заказ"), " ,чтобы перейти к выбору")
        markup.row(await create_button("Назад", ["main", "1", "0", "0", "0", "open"]),
                   await create_button("Собрать заказ", ["order", "3", "0", "0", "0", "open"]))
    else:
        info_text = fmt.text("\nНажмите ", fmt.hbold("Обновить"), "через несколько секунд")
        markup.row(await create_button("Назад", ["main", "1", "0", "0", "0", "open"]),
                   await create_button("Обновить", ["order", "2", "0", "0", "0", "update"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, orders_info, info_text, sep="\n")}


async def open_orders_menu(cll: CallbackQuery, state, action: str):
    markup = InlineKeyboardMarkup()

    if action == "open":
        orders_data = await db_query(func='fetch',
                                     sql="""WITH updated AS (UPDATE order_info SET status = $3, packer_id = $1
                                                                     WHERE status = $2 
                                                                     AND warehouse_id IN (SELECT warehouse_id 
                                                                                          FROM employee 
                                                                                          WHERE tg_id = $1) 
                                                                     RETURNING *)
                                                    SELECT u.posting_number, u.address, u.shipment_date, 
                                                    u.in_process_at, u.latitude, u.longitude, u.customer_name, 
                                                    u.customer_phone, u.customer_comment, count(o.name), sum(o.quantity)
                                                    FROM updated u, order_list o 
                                                    WHERE u.posting_number = o.posting_number AND u.status = $3
                                                    AND u.warehouse_id IN (SELECT warehouse_id FROM employee 
                                                                           WHERE tg_id = $1)
                                                    GROUP BY (u.posting_number, u.address, u.shipment_date, 
                                                              u.in_process_at, u.latitude, u.longitude, u.customer_name, 
                                                              u.customer_phone, u.customer_comment)
                                                    ORDER BY u.shipment_date;""",
                                     kwargs=[cll.from_user.id, 'awaiting_packaging', 'reserved_by_packer'])
        orders_data = orders_data[0]
    else:
        orders_data = await extra.save_previous(state=state, get=True)

    info_text = fmt.text("\nКоличество доступных заказов: ", fmt.hbold(len(orders_data)))

    await extra.save_previous(data_new=[dict(order) for order in orders_data], first=True, state=state)

    order_info = []
    for ind, order in enumerate(orders_data):
        order_info.append(fmt.text(fmt.text(fmt.hbold(f"\nЗаказ №{ind + 1}")),
                                   fmt.text(fmt.hbold("Номер отправления: "), order["posting_number"]),
                                   fmt.text(fmt.hbold("Товаров: "), order["sum"]),
                                   fmt.text(fmt.hbold("Адрес: "),
                                            fmt.hlink(order["address"], await extra.get_map_url(order["latitude"],
                                                                                                order["longitude"]))),
                                   sep="\n"))

        markup.row(await create_button(f"\nЗаказ №{ind + 1}\n",
                                       ["order", "4", ind, "0", order["posting_number"], "open"]))

    markup.row(await create_button("Назад", ["order", "2", "0", "0", "0", "back"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, info_text, *order_info, sep="\n")}


async def get_order_menu(callback, state):
    markup = InlineKeyboardMarkup()

    order_data = await extra.save_previous(state=state, get=True)
    order = order_data[int(callback["option"])]

    order_info = fmt.text(fmt.text(fmt.hbold("Номер отправления: "), order["posting_number"]),
                          fmt.text(fmt.hbold("\nВремя создания: "), order["in_process_at"]),
                          fmt.text(fmt.hbold("Время доставки"), order["shipment_date"]),
                          fmt.text(fmt.hbold("\nПокупатель: "), fmt.hitalic(order["customer_name"])),
                          fmt.text(fmt.hbold("Тел. покупателя:"), fmt.hcode(f"+{order['customer_phone']}")),
                          fmt.text(fmt.hbold("Коментарий: "), order["customer_comment"]),
                          fmt.text(fmt.hbold("\nАдрес: "), fmt.hlink(order["address"],
                                                                     await extra.get_map_url(order["latitude"],
                                                                                             order["longitude"]))),
                          fmt.text(fmt.hbold("\nПозиций: "), order["count"]),
                          fmt.text(fmt.hbold("Товаров: "), order["sum"]),
                          sep="\n")

    markup.row(await create_button("Назад", ["order", "3", "0", "0", "0", "back"]),
               await create_button("Сборка", ["order", "5", "0", "0", callback["item_id"], "open"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, order_info, sep="\n")}


async def get_package_order_menu(callback, cll: CallbackQuery, tz: str):
    markup = InlineKeyboardMarkup()

    if callback["action"] == "open":
        await db_query(func='execute',
                       sql="""WITH updated AS (UPDATE order_info SET status = $3, start_package_date = $7
                                                       WHERE posting_number = $1 RETURNING *)
                                      UPDATE order_info SET status = $4, packer_id = $6 WHERE status = $2 
                                      AND packer_id = $5 AND posting_number != $1;""",
                       kwargs=[callback["item_id"], 'reserved_by_packer', "packaging",
                               'awaiting_packaging', cll.from_user.id, None,
                               (await get_time(tz=tz)).replace(tzinfo=None)])
        await send_info_log(cll.message.chat.id, "Начал сборку",
                            fmt.text(fmt.hbold("Заказ: "), fmt.hcode(callback["item_id"])))

    order_info = await db_query(func='fetch',
                                sql="""SELECT * FROM order_list WHERE posting_number = $1 ORDER BY name;""",
                                kwargs=[callback["item_id"]])

    for ind, order in enumerate(order_info[0]):
        fact_quantity = order["fact_quantity"]
        if int(callback["option"]) == order["sku"]:
            if callback["action"] == "minus":
                print(order)
                if fact_quantity != 0:
                    fact_quantity -= 1

            elif callback["action"] == "plus":
                if fact_quantity < order["quantity"]:
                    fact_quantity += 1

            await db_query(func='execute',
                           sql="""UPDATE order_list SET fact_quantity = $2 
                                          WHERE name = $1 AND posting_number = $3;""",
                           kwargs=[order["name"], fact_quantity, callback["item_id"]])

        more = f"{order['quantity']} -> " if order["quantity"] < fact_quantity else ""
        less = f" <- {order['quantity']}" if order["quantity"] > fact_quantity else ""
        name_product = order['name'].split(', ')
        markup.row(await create_button(f"{ind + 1}. {name_product[-1]}, {', '.join(name_product[:-1])}",
                                       ["order", "6", order["sku"], "0", callback["item_id"], "open"]))
        markup.row(await create_button("-", ["order", "5", order["sku"], "0", callback["item_id"], "minus"]),
                   await create_button(f"{more}{fact_quantity}{less}", ["order", "4", order["sku"], "0",
                                                                                 callback["item_id"], "pass"]),
                   await create_button("+", ["order", "5", order["sku"], "0", callback["item_id"], "plus"]))
    markup.row(await create_button("Отменить", ["order", "6", "0", "0", callback["item_id"], "cancel"]),
               await create_button("Собран", ["order", "7", "0", "0", callback["item_id"], "open"]))

    return {"reply_markup": markup}


async def get_product_id_menu(cll: CallbackQuery = None, state=None):
    if cll:
        await extra.save_previous(cll.message.html_text, cll.message.reply_markup, state=state)

        markup = InlineKeyboardMarkup()

        info = await request.get_info(cll.from_user.id, int(cll.data.split(":")[-4]))
        order_info = fmt.text(fmt.text(""), fmt.hbold("\nШтрих-код: "), info["barcode"],
                              fmt.hide_link(info["primary_image"]))

        markup.row(await create_button("Свернуть", ["order", "6", "0", "0", cll.data.split(":")[-2], "back"]))

        return {"reply_markup": markup, "text": fmt.text(menu_name, order_info, sep="\n")}

    else:
        return await extra.save_previous(state=state, get=True, menu=True)


async def get_reasons_for_cancel_menu(cll: CallbackQuery = None, state=None):
    if cll:
        await extra.save_previous(cll.message.html_text, cll.message.reply_markup, state=state)

        markup = InlineKeyboardMarkup()

        order_info = fmt.text(fmt.text(f"\nОтмена заказа", fmt.hbold(cll.data.split(":")[-2])),
                              fmt.text("\nВыберете причину или введите свою, нажав ", fmt.hbold("Другая причина")),
                              sep="\n")

        for key, item in CANCELLATION_STATUS.items():
            if key == 402:
                markup.row(await create_button(item.capitalize(),
                                               ["order", "6", key, "0", cll.data.split(":")[-2], "future"]))
            else:
                markup.row(await create_button(item.capitalize(),
                                               ["order", "3", key, "0", cll.data.split(":")[-2], "cancel"]))

        markup.row(await create_button("Назад", ["order", "6", "0", "0", cll.data.split(":")[-2], "back"]))

        return {"reply_markup": markup, "text": fmt.text(menu_name, order_info, sep="\n")}

    else:
        return await extra.save_previous(state=state, get=True, menu=True)


async def get_pre_complete_menu(cll: CallbackQuery = None, state=None):
    if cll:
        await extra.save_previous(cll.message.html_text, cll.message.reply_markup, state=state)

        markup = InlineKeyboardMarkup()

        callback = cll.data.split(":")

        order_info = await db_query(func='fetch',
                                    sql="""SELECT * 
                                           FROM order_list 
                                           WHERE posting_number = $1 
                                           ORDER BY name;""",
                                    kwargs=[callback[5]])

        products = []
        for ind, order in enumerate(order_info[0]):
            if ind in [0, len(order_info[0])]:
                products.append('=' * 30)
            else:
                products.append('-' * 30)
            products.append(fmt.text(f'{ind + 1}. {order["name"]}\nЗаказано: {order["quantity"]}, Собрано: ',
                            fmt.hcode(f'{order["fact_quantity"]}') if order["quantity"] != order["fact_quantity"] else fmt.text(f'{order["fact_quantity"]}')))

        # should_be = 0
        # in_fact = 0
        # for ind, order in enumerate(order_info[0]):
        #     should_be += order["quantity"]
        #     in_fact += order["fact_quantity"]
        #
        # products = fmt.text(f'\nЗаказано: {should_be}\nСобрано: ', fmt.hcode(f'{in_fact}') if should_be != in_fact else fmt.text(f'{in_fact}'))

        markup.row(await create_button("Назад", ["order", "7", "0", "0", callback[5], "back"]),
                   await create_button("Подтвердить", ["order", "8", "0", "0", callback[5], "complete"]))

        return {"reply_markup": markup, "text": fmt.text(menu_name, *products, sep="\n")}

    else:
        return await extra.save_previous(state=state, get=True, menu=True)


async def get_complete_menu(cll: CallbackQuery, tz: str):
    markup = InlineKeyboardMarkup()

    order_info = await db_query(func='fetch',
                                sql="""SELECT * FROM order_list WHERE posting_number = $1 ORDER BY name;""",
                                kwargs=[cll.data.split(":")[-2]])

    status, posting_number = await request.complete_packaging_ozon(order_info[0], cll.from_user.id)

    info_text = fmt.text(f"\nПоздравляем! Вы успешно завершили сборку заказа", fmt.hbold(posting_number))

    markup.row(await create_button("Готово", ["order", "2", "0", "0", "0", "complete"]))

    await finish_state(cll.message.chat.id, cll.from_user.id)

    await send_info_log(cll.message.chat.id, "завершил сборку",
                        fmt.text(fmt.text(fmt.hbold("Заказ: "), fmt.hcode(posting_number)),
                                 fmt.text(fmt.hbold("\nСобран: "), "Частично" if status else "Полностью")))

    if status:
        await db_query(func="execute",
                       sql="""WITH updated AS (UPDATE order_info 
                                                       SET status = $2, finish_package_date = $3, 
                                                       cancel_reason_id = $5, cancel_reason = $6, 
                                                       cancellation_type = $7, cancellation_initiator = $8
                                                       WHERE posting_number = $1 RETURNING *)
                                      INSERT INTO logs_status_changes (date, status, status_ozon_seller, posting_number)
                                      VALUES($3, $2, $4, $1);""",
                       kwargs=[cll.data.split(":")[-2], "canceled", (await get_time(tz=tz)).replace(tzinfo=None),
                               "canceled", 352, CANCELLATION_STATUS[352], "seller", "Продавец"])
    else:
        await db_query(func='execute',
                       sql="""WITH updated AS (UPDATE order_info SET status = $2, finish_package_date = $3
                                               WHERE posting_number = $1 RETURNING *)
                                      INSERT INTO logs_status_changes (date, status, status_ozon_seller, posting_number)
                                      VALUES($3, $2, $4, $1);""",
                       kwargs=[cll.data.split(":")[-2], 'awaiting_deliver',
                               (await get_time(tz=tz)).replace(tzinfo=None), 'awaiting_deliver'])

    return {"reply_markup": markup, "text": fmt.text(menu_name, info_text, sep="\n")}
