from utils.db.database import db_query
from utils.proccess_time import get_time


# ****************************************logs_bot_running****************************************
async def write_bot_start_status() -> None:
    await db_query(func='execute',
                   sql="""INSERT INTO logs_bot_running (start_date) VALUES($1);""",
                   kwargs=[await get_time()])
    return


async def write_bot_finish_status() -> None:
    await db_query(func='execute',
                   sql="""UPDATE logs_bot_running SET finish_date = $1 
                                              WHERE id = (SELECT max(id) FROM logs_bot_running);""",
                   kwargs=[await get_time()])
    return


# ****************************************api****************************************
async def get_sellers_api_info() -> list:
    sellers_info = await db_query(func='fetch',
                                  sql="""SELECT * FROM api
                                         WHERE status = $1;""",
                                  kwargs=["active"])
    return sellers_info[0]


async def get_api_info(tg_id: int) -> dict:
    api = await db_query(func='fetch',
                         sql="""SELECT * 
                                FROM api 
                                WHERE seller_id = (SELECT seller_id 
                                                   FROM employee 
                                                   WHERE tg_id = $1);""",
                         kwargs=[tg_id])

    return dict(api[0][0])


async def create_new_api(dct: dict) -> None:
    await db_query(func='execute',
                   sql="""INSERT INTO api 
                          (seller_id, api_key, seller_name, timezone, log_chat_id, warehouse_id)
                          VALUES($1, $2, $3, $4, $5, $6) 
                          ON CONFLICT (warehouse_id) DO NOTHING;""",
                   kwargs=[dct['seller_id'], dct['api_key'], dct['seller_name'],
                           dct['timezone'], dct['log_chat_id'], dct['warehouse_id']])
    return


async def update_api_key(api_key: str, seller_id: int) -> None:
    await db_query(func='execute',
                   sql="""UPDATE api 
                          SET api_key = $1 
                          WHERE seller_id = $2;""",
                   kwargs=[api_key, seller_id])
    return


# ****************************************employee****************************************
async def get_employee_info_to_edit_msg(tg_id: int) -> dict:
    order_info = await db_query(func="fetch",
                                sql="""SELECT e.tg_id, e.msg_id, e.function, e.status, e.state, a.timezone 
                                       FROM employee e, api a
                                       WHERE a.seller_id=e.seller_id AND e.tg_id = $1 AND e.state = $2
                                       AND a.seller_id IN (SELECT seller_id 
                                                           FROM employee
                                                           WHERE tg_id = $1 AND state = $2);""",
                                kwargs=[tg_id, "activated"])
    return order_info[0][0]


async def get_user_info(tg_id: int = None, user_id: int = None) -> dict:
    if tg_id:
        user_id, extra = tg_id, "tg_"
    else:
        extra = ""

    try:
        user_info = await db_query(func='fetch',
                                   sql=f"""SELECT e.*, a.name AS added_by_name
                                           FROM employee e, employee a
                                           WHERE e.{extra}id = $1 AND e.added_by_id = a.tg_id
                                           LIMIT 1;""",
                                   kwargs=[user_id])
        return user_info[0][0]
    except IndexError:
        return {'username': "Отсутствует"}


async def get_users_info(tg_id: int, function: str) -> list:
    user_info = await db_query(func='fetch',
                               sql="""SELECT name, id 
                                      FROM employee 
                                      WHERE function = $2 
                                      AND state != $3
                                      AND warehouse_id IN (SELECT warehouse_id 
                                                           FROM employee 
                                                           WHERE tg_id = $1);""",
                               kwargs=[tg_id, function, 'удален'])  # Исправить
    return user_info[0]


async def update_msg(message_id: int, chat_id: int):
    old_msg_id = await db_query(func='fetch',
                                sql="""UPDATE employee 
                                       SET msg_id = $1 
                                       WHERE tg_id = $2 AND state != $3
                                       RETURNING (SELECT msg_id 
                                                  FROM employee 
                                                  WHERE tg_id = $2 AND state != $3);""",
                                kwargs=[message_id, chat_id, 'удален'])  # Исправить
    return old_msg_id[0][0]['msg_id']


async def update_employee_last_status(args: list, ex_parameters: list = None) -> None:
    await db_query(func='execute',
                   sql=f"""WITH updated AS (UPDATE employee 
                                            SET status = $2 
                                            WHERE tg_id = $1 
                                            RETURNING *)
                           INSERT INTO logs_status_changes 
                           (employee_id, status, date{ex_parameters[1] if ex_parameters else ""}) 
                           VALUES($1, $2, $3{ex_parameters[0] if ex_parameters else ""});""",
                   kwargs=[*args])
    return


async def get_last_msg(tg_id: int):
    msg_id = await db_query(func='fetch',
                            sql="""SELECT msg_id 
                                   FROM employee 
                                   WHERE tg_id = $1 AND state != $2;""",
                            kwargs=[tg_id, 'удален'])  # Исправить
    return msg_id[0][0]['msg_id']


async def get_info_for_protection(user_id: int):
    user_info = await db_query(func="fetch",
                               sql="""SELECT e.function, e.status, e.state, a.timezone FROM employee e, api a
                                      WHERE a.seller_id=e.seller_id AND e.tg_id = $1 AND e.state = $2
                                      AND a.seller_id IN (SELECT seller_id FROM employee
                                                          WHERE tg_id = $1 AND state = $2);""",
                               kwargs=[user_id, "activated"])
    return user_info[0][0]


async def register_new_moderator(uuid: str, name: str, function: str, tg_id: int):
    await db_query(func='execute',
                   sql="""INSERT INTO employee 
                          (uuid, state, name, function, added_by_id) 
                          VALUES($1, $2, $3, $4, $5);""",
                   kwargs=[uuid, 'awaiting_activating', name, function, tg_id])


async def register_new_admin(uuid: str, name: str, function: str, tg_id: int,
                             phone: str, warehouse_id: int, seller_id: int) -> None:
    await db_query(func='execute',
                   sql="""INSERT INTO employee 
                          (uuid, state, name, function, added_by_id, phone, warehouse_id, seller_id)
                          VALUES($1, $2, $3, $4, $5, $6, $7, $8);""",
                   kwargs=[uuid, 'awaiting_activating', name, function, tg_id,
                           phone, warehouse_id, seller_id])


async def register_new_employee(uuid: str, name: str, function: str, tg_id: int, phone: str) -> None:
    await db_query(func='execute',
                   sql="""INSERT INTO employee 
                          (uuid, state, name, function, added_by_id, phone, warehouse_id, seller_id)
                          VALUES($1, $2, $3, $4, $5, $6, 
                                 (SELECT warehouse_id FROM employee WHERE tg_id = $5), 
                                 (SELECT seller_id FROM employee WHERE tg_id = $5));""",
                   kwargs=[uuid, 'awaiting_activating', name, function, tg_id, phone])
    return


async def end_registration_new_user(uuid: str, tg_id: int, username) -> None:
    await db_query(func="execute",
                   sql="""WITH src AS (INSERT INTO employee_stat
                                       (tg_id, orders_number, successful, unsuccessful)
                                       VALUES($2, 0, 0, 0) ON CONFLICT (tg_id) DO NOTHING
                                       RETURNING *)
                          UPDATE employee
                          SET tg_id = $2, username = $3, state = $4, begin_date = $6, status = $7
                          WHERE uuid = $1 AND state = $5;""",
                   kwargs=[uuid, tg_id, username, "activated", "awaiting_activating", await get_time(), "not_on_shift"])
    return


async def register_new_creator(uuid: str, tg_id: int, username) -> None:
    await db_query(func="execute",
                   sql="""INSERT INTO employee 
                          (uuid, tg_id, username, state, function, begin_date)
                          VALUES($1, $2, $3, $4, $5, $6) ON CONFLICT (uuid) DO NOTHING;""",
                   kwargs=[uuid, tg_id, username, "activated", "creator", await get_time()])
    return


async def delete_employee(tg_id: int) -> None:
    await db_query(func='execute',
                   sql="""UPDATE employee 
                          SET state = $1, end_date = $2 
                          WHERE id = $3;""",
                   kwargs=['удален', await get_time(), tg_id])
    return


# ****************************************order_info****************************************
async def get_orders_last_day_info(tg_id: int, tz: str) -> list:
    orders_info = await db_query(func='fetch',
                                 sql="""SELECT * 
                                        FROM order_info 
                                        WHERE in_process_at > $2 
                                        AND warehouse_id IN (SELECT warehouse_id 
                                                             FROM employee 
                                                             WHERE tg_id = $1);""",
                                 kwargs=[tg_id, (await get_time(24, minus=True, tz=tz)).replace(tzinfo=None)])
    return orders_info[0] if orders_info else []


async def get_order_info(posting_number: str):
    order_info = await db_query(func='fetch',
                                sql="""SELECT u.*, count(o.name), sum(o.quantity)
                                        FROM order_info u, order_list o
                                        WHERE u.posting_number = o.posting_number 
                                        AND u.posting_number = $1
                                        GROUP BY (u.posting_number, u.address, u.shipment_date, 
                                                  u.in_process_at, u.latitude, u.longitude, 
                                                  u.customer_name, u.customer_phone, u.customer_comment)
                                        ORDER BY u.shipment_date""",
                                kwargs=[posting_number])
    return order_info[0][0]


async def get_order_info_by_order_number(order_number: str):
    order_info = await db_query(func='fetch',
                                sql="""SELECT u.*, count(o.name), sum(o.quantity)
                                        FROM order_info u, order_list o
                                        WHERE u.posting_number = o.posting_number 
                                        AND u.order_number = $1
                                        GROUP BY (u.posting_number, u.address, u.shipment_date, 
                                                  u.in_process_at, u.latitude, u.longitude, 
                                                  u.customer_name, u.customer_phone, u.customer_comment)
                                        ORDER BY u.shipment_date""",
                                kwargs=[order_number])
    return order_info[0][0] if order_info[0] else None


async def get_order_msg_id(posting_number: str = None, order_number: str = None):
    option = "order_number" if order_number else "posting_number"
    order_info = await db_query(func='fetch',
                                sql=f"""SELECT message_id
                                        FROM order_info
                                        WHERE {option} = $1
                                        LIMIT 1;""",
                                kwargs=[order_number if order_number else posting_number])
    return order_info[0][0]["message_id"]


async def get_orders_info_for_polling(warehouse_id: int):
    orders_info = await db_query(func='fetch',
                                 sql="""SELECT posting_number, status_api, cancel_reason_id, status, 
                                               start_delivery_date, current_status, order_number
                                        FROM order_info 
                                        WHERE warehouse_id = $1 
                                        AND in_process_at > $2 
                                        ORDER BY shipment_date;""",
                                 kwargs=[warehouse_id, (await get_time(36, minus=True))])
    return orders_info[0]


async def get_order_info_for_cancelling(posting_number: str) -> dict:
    order_info = await db_query(func="fetch",
                                sql="""SELECT packer_id, start_package_date, finish_package_date, 
                                              deliver_id, start_delivery_date, finish_delivery_date,
                                              address, posting_number
                                       FROM order_info 
                                       WHERE posting_number = $1;""",
                                kwargs=[posting_number])
    return order_info[0][0]


async def get_order_info_for_delivering(posting_number):
    order = await db_query(func='fetch',
                           sql="""SELECT posting_number, address, shipment_date, latitude, longitude
                                  FROM order_info 
                                  WHERE posting_number = $1 AND status = $2;""",
                           kwargs=[posting_number, 'reserved_by_deliver'])

    return order[0][0]


async def create_new_order(order: dict, in_process_at, shipment_date, current_time) -> None:
    await db_query(func='execute',
                   sql="""WITH src AS (INSERT INTO order_info 
                                       (posting_number, order_id, order_number, warehouse_id, status, 
                                        status_api, address, zip_code, latitude, longitude, 
                                        customer_id, customer_name, customer_phone, customer_email, 
                                        customer_comment, addressee_name, addressee_phone, 
                                        in_process_at, shipment_date, 
                                        cancel_reason_id, cancel_reason, cancellation_type, 
                                        cancelled_after_ship, affect_cancellation_rating, 
                                        cancellation_initiator)
                                       VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, 
                                              $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25)
                                       ON CONFLICT (posting_number) DO UPDATE
                                       SET status_api = $6, customer_comment = $15, cancel_reason_id = $20, 
                                           cancel_reason = $21, cancellation_type = $22, cancelled_after_ship = $23, 
                                           affect_cancellation_rating = $24, cancellation_initiator = $25
                                       RETURNING *)
                          INSERT INTO logs_status_changes 
                          (date, status, status_ozon_seller, posting_number) 
                          VALUES($26, $5, $6, $1);""",
                   kwargs=[order['posting_number'], order['order_id'], order['order_number'],
                           order['delivery_method']['warehouse_id'], order["status"], order["status"],
                           order['customer']['address']['address_tail'], order['customer']['address']['zip_code'],
                           float(order['customer']['address']['latitude']),
                           float(order['customer']['address']['longitude']),
                           order['customer']['customer_id'], order['customer']['name'], order['customer']['phone'],
                           order['customer']['customer_email'], order['customer']['address']['comment'],
                           order['addressee']['name'], order['addressee']['phone'], in_process_at, shipment_date,
                           order['cancellation']['cancel_reason_id'], order['cancellation']['cancel_reason'],
                           order['cancellation']['cancellation_type'], order['cancellation']['cancelled_after_ship'],
                           order['cancellation']['affect_cancellation_rating'],
                           order['cancellation']['cancellation_initiator'], current_time])
    return


async def insert_order_message_id(posting_number: str, message_id: int, channel_id: str) -> None:
    await db_query(func='execute',
                   sql="""UPDATE order_info 
                          SET message_channel_id = $2, channel_id = $3
                          WHERE posting_number = $1;""",
                   kwargs=[posting_number, message_id, channel_id])
    return


async def insert_message_id(message_id: int, message_channel_id: int) -> None:
    await db_query(func='execute',
                   sql="""UPDATE order_info 
                          SET message_id = $2
                          WHERE message_channel_id = $1;""",
                   kwargs=[message_id, message_channel_id])
    return


async def update_order_last_status(new_status: str, posting_number: str, tz: str) -> str:
    await db_query(func='execute',
                   sql="""WITH updated AS (UPDATE order_info 
                                           SET status = $2
                                           WHERE posting_number = $1 
                                           RETURNING *)
                          INSERT INTO logs_status_changes
                          (posting_number, status_ozon_seller, date, status)
                          VALUES($1, $2, $3, $4);""",
                   kwargs=[posting_number, new_status, (await get_time(tz=tz)).replace(tzinfo=None), new_status])

    status = await db_query(func='fetch',
                            sql="""SELECT status
                                   FROM order_info 
                                   WHERE posting_number = $1
                                   LIMIT 1;""",
                            kwargs=[posting_number])
    return status[0][0]["status"]


async def count_orders(tg_id: int, status: str) -> int:
    count = await db_query(func='fetch',
                           sql="""SELECT count(posting_number) 
                                  FROM order_info 
                                  WHERE status = $2 
                                  AND warehouse_id IN (SELECT warehouse_id 
                                                       FROM employee 
                                                       WHERE tg_id = $1);""",
                           kwargs=[tg_id, status])
    return count[0][0]["count"]


async def get_reserved_user(tg_id: int, status: str) -> list:
    names = await db_query(func='fetch',
                           sql="""SELECT name 
                                  FROM employee 
                                  WHERE status = $2 
                                  AND warehouse_id IN (SELECT warehouse_id 
                                                       FROM employee 
                                                       WHERE tg_id = $1);""",
                           kwargs=[tg_id, status])
    return names[0]


async def reserve_orders_for_package(tg_id: int) -> list:
    orders_data = await db_query(func='fetch',
                                 sql="""WITH updated AS (UPDATE order_info 
                                                         SET status = $3, packer_id = $1
                                                         WHERE status = $2 
                                                         AND warehouse_id IN (SELECT warehouse_id 
                                                                              FROM employee 
                                                                              WHERE tg_id = $1)
                                                         RETURNING *)
                                        SELECT u.posting_number, u.address, u.shipment_date, u.in_process_at, 
                                               u.latitude, u.longitude, u.customer_name, u.customer_phone, 
                                               u.customer_comment, count(o.name), sum(o.quantity)
                                        FROM updated u, order_list o 
                                        WHERE u.posting_number = o.posting_number 
                                        AND u.status = $3
                                        AND u.warehouse_id IN (SELECT warehouse_id 
                                                               FROM employee 
                                                               WHERE tg_id = $1)
                                        GROUP BY (u.posting_number, u.address, u.shipment_date, 
                                                  u.in_process_at, u.latitude, u.longitude, 
                                                  u.customer_name, u.customer_phone, u.customer_comment)
                                        ORDER BY u.shipment_date
                                        LIMIT 5;""",
                                 kwargs=[tg_id, 'awaiting_packaging', 'reserved_by_packer'])
    return orders_data[0]


async def reserve_orders_for_delivery(tg_id: int, limit: int = None) -> list:
    orders_info = await db_query(func='fetch',
                                 sql="""WITH updated AS (UPDATE order_info 
                                                         SET status = $3, deliver_id = $1 
                                                         WHERE status = $2
                                                         AND warehouse_id IN (SELECT warehouse_id 
                                                                              FROM employee 
                                                                              WHERE tg_id = $1)
                                                         RETURNING *)
                                         SELECT posting_number, address, shipment_date
                                         FROM updated
                                         ORDER BY shipment_date
                                         LIMIT $4;""",
                                 kwargs=[tg_id, "awaiting_deliver", 'reserved_by_deliver', limit if limit else 5])

    return orders_info[0]


async def reset_reserve_status(function_id: str, args: list) -> None:
    await db_query(func='execute',
                   sql=f"""UPDATE order_info 
                           SET status = $3, {function_id} = $4 
                           WHERE status = $2 AND {function_id} = $1;""",
                   kwargs=[*args])
    return


async def start_package_order(posting_number: str, tg_id: str, tz: str) -> None:
    await db_query(func='execute',
                   sql="""WITH updated AS (UPDATE order_info 
                                           SET status = $3, start_package_date = $7
                                           WHERE posting_number = $1 
                                           RETURNING *)
                          UPDATE order_info 
                          SET status = $4, packer_id = $6 
                          WHERE status = $2 
                          AND packer_id = $5 
                          AND posting_number != $1;""",
                   kwargs=[posting_number, 'reserved_by_packer', "packaging", 'awaiting_packaging',
                           tg_id, None, (await get_time(tz=tz)).replace(tzinfo=None)])
    return


async def complete_package(posting_number: str, tz: str):
    await db_query(func='execute',
                   sql="""WITH updated AS (UPDATE order_info 
                                           SET status = $2, finish_package_date = $3
                                           WHERE posting_number = $1 
                                           RETURNING *)
                          INSERT INTO logs_status_changes 
                          (date, status, status_ozon_seller, posting_number)
                          VALUES($3, $2, $4, $1);""",
                   kwargs=[posting_number, 'awaiting_deliver',
                           (await get_time(tz=tz)).replace(tzinfo=None), 'awaiting_deliver'])


async def cancel_order(posting_number: str, tz: str) -> None:
    from data.condition import CANCELLATION_STATUS

    await db_query(func="execute",
                   sql="""WITH updated AS (UPDATE order_info 
                                           SET status = $2, finish_package_date = $3, 
                                               cancel_reason_id = $5, cancel_reason = $6, 
                                               cancellation_type = $7, cancellation_initiator = $8
                                           WHERE posting_number = $1 
                                           RETURNING *)
                          INSERT INTO logs_status_changes 
                          (date, status, status_ozon_seller, posting_number)
                          VALUES($3, $2, $4, $1);""",
                   kwargs=[posting_number, "canceled", (await get_time(tz=tz)).replace(tzinfo=None),
                           "canceled", 352, CANCELLATION_STATUS[352], "seller", "Продавец"])
    return


async def start_delivery_order(list_of_orders: list, tg_id: int, tz: str) -> list:
    already_added = (await db_query(func='fetch',
                                    sql="""SELECT order_id, posting_number, address, addressee_name, 
                                                  addressee_phone, customer_comment, shipment_date, 
                                                  latitude, longitude
                                           FROM order_info 
                                           WHERE status = $2 
                                           AND warehouse_id IN (SELECT warehouse_id 
                                                                FROM employee 
                                                                WHERE tg_id = $1)
                                           AND deliver_id = $1
                                           AND start_delivery_date > $3;""",
                                    kwargs=[tg_id, 'delivering',
                                            (await get_time(1, tz=tz, minus=True)).replace(tzinfo=None)]))[0]
    info = await db_query(func='fetch',
                          sql="""WITH updated AS (UPDATE order_info 
                                                  SET status = $3, start_delivery_date = $5
                                                  WHERE posting_number = ANY($1)
                                                  AND deliver_id = $2 
                                                  AND status_api = $4
                                                  RETURNING *)
                                 SELECT order_id, posting_number, address, addressee_name, 
                                        addressee_phone, customer_comment, shipment_date, 
                                        latitude, longitude
                                 FROM updated 
                                 WHERE status = $3 AND warehouse_id IN (SELECT warehouse_id 
                                                                        FROM employee 
                                                                        WHERE tg_id = $2);""",
                          kwargs=[tuple(list_of_orders), tg_id, 'delivering', 'awaiting_deliver',
                                  (await get_time(tz=tz)).replace(tzinfo=None)])
    all_info = list(already_added)
    all_info.extend(info[0])
    await update_employee_last_status([tg_id, 'delivering' if len(all_info) > 0 else 'on_shift', await get_time(tz=tz)])
    return all_info


async def complete_posting_delivery(posting_number: str, tg_id: int, tz: str, location: dict, result: str) -> None:
    await db_query(func='execute',
                   sql="""WITH updated AS (UPDATE order_info 
                                           SET status = $4, finish_delivery_date = $3, 
                                               finish_delivery_latitude = $6, finish_delivery_longitude = $7
                                           WHERE posting_number = $1 
                                           RETURNING *)
                          INSERT INTO logs_status_changes
                          (posting_number, status_ozon_seller, date, status, employee_id, latitude, longitude)
                          VALUES($1, $2, $3, $4, $5, $6, $7);""",
                   kwargs=[posting_number, 'delivering', (await get_time(tz=tz)).replace(tzinfo=None), result,
                           tg_id, location['latitude'], location['longitude']])
    return


async def write_current_status(post_: str, current_status: str) -> None:
    await db_query(func='execute',
                   sql=f"""UPDATE order_info 
                           SET current_status = $2
                           WHERE posting_number = $1;""",
                   kwargs=[post_, current_status])
    return


# ****************************************logs_button_clicks****************************************
async def log_entry(new_obj, btn=None) -> None:
    obj = new_obj.message if btn else new_obj

    await db_query(func="execute",
                   sql="""INSERT INTO logs_button_clicks 
                          (date, tg_id, chat_id, message_id, from_user_tg_id, 
                          first_name, last_name, username, button_name, button_data)
                          VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
                   kwargs=[await get_time(), new_obj.from_user.id, obj.chat.id, obj.message_id, obj.chat.id,
                           obj.from_user.first_name, obj.from_user.last_name, obj.from_user.username,
                           btn if btn else obj.text, new_obj.data if btn else 'None'])
    return


# ****************************************logs_errors****************************************
async def write_error_log(error_name: str, tz: str = "Europe/Moscow", error_type: str = None, user_id: str = None,
                          posting_number: str = None, warehouse_id: int = None, description: str = None) -> None:
    await db_query(func='execute',
                   sql="""INSERT INTO logs_errors 
                          (date, error_name, type, user_id, posting_number, warehouse_id, description) 
                          VALUES($1, $2, $3, $4, $5, $6, $7);""",
                   kwargs=[await get_time(tz=tz), error_name, error_type, user_id,
                           posting_number, warehouse_id, description])
    return


async def get_first_time_error(posting_number: str, warehouse_id: int):
    count = await db_query(func='fetch',
                           sql="""SELECT MIN(date) AS date, COUNT(date)
                                  FROM logs_errors 
                                  WHERE posting_number = $1 
                                  AND warehouse_id = $2 
                                  AND type = $3
                                  GROUP BY warehouse_id
                                  ORDER BY date
                                  LIMIT 1;""",
                           kwargs=[posting_number, warehouse_id, "TypeError"])
    return count[0][0]


# ****************************************logs_status_changes****************************************


# ****************************************order_list****************************************
async def create_new_products(order: dict, products_info: dict) -> None:
    for product in order['products']:
        extra_info = products_info[str(product['sku'])]
        barcode = int(extra_info["barcode"] if extra_info["barcode"] else 0)
        await db_query(func='execute',
                       sql="""INSERT INTO order_list 
                              (order_id, posting_number, sku, name, offer_id, quantity, price, fact_quantity, changed,
                               volume_weight, category_id, product_id, barcode, primary_image, rank) 
                              VALUES($1, $2, $3, $4, $5, $6, $7, $6, $8, $9, $10, $11, $12, $13, $14);""",
                       kwargs=[order['order_id'], order['posting_number'], int(product['sku']), product['name'],
                               product['offer_id'], product['quantity'], float(product['price']), False,
                               extra_info["volume_weight"], extra_info["category_id"], extra_info["product_id"],
                               barcode, extra_info["primary_image"], extra_info["rank"]])
    return


async def update_product_fact_quantity(name, fact_quantity, posting_number) -> None:
    await db_query(func='execute',
                   sql="""UPDATE order_list 
                          SET fact_quantity = $2 
                          WHERE name = $1 
                          AND posting_number = $3;""",
                   kwargs=[name, fact_quantity, posting_number])
    return


async def update_product_weight(sku: int, weight: int, posting_number: str) -> None:
    weight = weight if weight != 0 else None
    await db_query(func='execute',
                   sql="""UPDATE order_list 
                          SET weight = $2 
                          WHERE sku = $1 
                          AND posting_number = $3;""",
                   kwargs=[sku, weight, posting_number])
    return


async def get_products_info(posting_number: str) -> list:
    order_info = await db_query(func='fetch',
                                sql="""SELECT * 
                                       FROM order_list 
                                       WHERE posting_number = $1 
                                       ORDER BY name;""",
                                kwargs=[posting_number])
    return order_info[0]


async def get_product_name(posting_number: str, sku: int) -> list:
    order_info = await db_query(func='fetch',
                                sql="""SELECT name 
                                       FROM order_list 
                                       WHERE posting_number = $1 
                                       AND sku = $2;""",
                                kwargs=[posting_number, sku])
    return order_info[0][0]["name"]


# ****************************************employee_stat****************************************


# ****************************************customer_stat****************************************


# ****************************************finite_state_machine****************************************
async def save_callback(cll, tz):
    await db_query(func="execute",
                   sql="""INSERT INTO finite_state_machine 
                          (tg_id, message_id, chat_id, text, entities, reply_markup, data, date)
                          VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
                   kwargs=[cll.message.chat.id, cll.message.message_id, cll.message.chat.id, cll.message.text,
                           cll.message.entities, cll.message.reply_markup, cll.data, await get_time(tz=tz)])


# ****************************************routing****************************************
async def get_product_rank(category_id: int) -> int:
    order_info = await db_query(func='fetch',
                                sql="""SELECT total_rank 
                                       FROM routing 
                                       WHERE under_child_category_id = $1
                                       LIMIT 1;""",
                                kwargs=[category_id])
    return order_info[0][0]["total_rank"] if order_info[0] else int(1001001)


async def get_product_category_name(rank: int) -> int:
    order_info = await db_query(func='fetch',
                                sql="""SELECT child_category_name 
                                       FROM routing 
                                       WHERE total_rank = $1
                                       LIMIT 1;""",
                                kwargs=[rank])
    return order_info[0][0]["child_category_name"]


# ****************************************tags****************************************
async def write_tag(order_number: str, tz: str, tag_: str) -> list:
    result = await db_query(func='fetch',
                            sql="""WITH src AS (INSERT INTO tags 
                                                (date, posting_number, hashtag) 
                                                VALUES($1, $2, $3)
                                                RETURNING *)
                                   SELECT hashtag
                                   FROM tags
                                   WHERE posting_number = $2;""",
                            kwargs=[await get_time(tz=tz), order_number, tag_])
    lst = result[0]
    return [tag["hashtag"] for tag in lst] if lst else []


async def get_tags(order_number: str) -> list:
    result = await db_query(func='fetch',
                            sql="""SELECT hashtag 
                                   FROM tags 
                                   WHERE posting_number = $1;""",
                            kwargs=[order_number])
    lst = result[0]
    return [tag["hashtag"] for tag in lst] if lst else []


if __name__ == '__main__':
    pass
