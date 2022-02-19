import aiohttp
from aiohttp.client_exceptions import ContentTypeError, ServerDisconnectedError, ClientResponseError, \
    ClientConnectorError
import asyncio
import aiogram.utils.markdown as fmt
import logging

from loader import dp
from data.condition import ORDER_STATE, API_METHODS
from data.config import API_URL, USER_AGENT, DEBUG, MODER_LOGS
from utils.db_api.database import db_query
from utils.proccess_time import get_time, change_dt_api_format


async def start_polling():
    try:
        logging.info('Старт опроса API')
        asyncio.create_task(main())

    except Exception as e:
        print(e)


async def main():
    while True:
        try:
            await asyncio.sleep(5)
            sellers = await db_query(func='fetch',
                                     sql="""SELECT * FROM api;""",
                                     kwargs=[])
            for seller in sellers[0]:
                await check_response(await get_api_response(seller), seller)

        except asyncio.CancelledError:
            logging.info('Завершение опроса API')
            return False

        except ConnectionError:
            logging.error(ConnectionError)
            await asyncio.sleep(15)

        except ContentTypeError:
            logging.error(ContentTypeError)


async def get_api_response(seller):
    try:

        async with aiohttp.ClientSession() as session:
            try:

                async with session.post(**await get_unfulfilled_list(seller)) as response:
                    try:
                        result = await response.json()
                        result = result["result"]["postings"]

                    except ContentTypeError:
                        logging.error(ContentTypeError)
                        result = []

                    finally:
                        return result

            except (TimeoutError, ValueError) as error_1:
                logging.error(error_1)

    except (ServerDisconnectedError, ClientResponseError, ClientConnectorError) as error_2:
        logging.error(error_2)
        pass


async def get_unfulfilled_list(api):
    param = {"url": API_URL + API_METHODS["v6"],
             "headers": {"User-Agent": USER_AGENT,
                         "Client-Id": str(api["seller_id"]), "Api-Key": api["api_key"]},
             "json": {"dir": "ASC",
                      "filter": {"since": (await get_time(n=24, minus=True)).strftime("%Y-%m-%dT%H:%M:%S.00Z"),
                                 "to": (await get_time(n=24, plus=True)).strftime("%Y-%m-%dT%H:%M:%S.00Z")},
                      "limit": 1000,
                      "offset": 0}}
    return param


async def check_response(response, seller):
    if DEBUG:
        logging.info(len(response))

    if response:
        exists_orders = await db_query(func='fetch',
                                       sql="""SELECT posting_number, status, cancel_reason_id  FROM order_info 
                                                      WHERE warehouse_id = $1 ORDER BY shipment_date;""",
                                       kwargs=[seller["warehouse_id"]])

        for order_info in response:
            try:
                if order_info["posting_number"] not in [order["posting_number"] for order in exists_orders[0]]:
                    logging.info(f"NEW ORDER {order_info['posting_number']}")
                    await change_order(order_info, seller, new=True)

                else:
                    for exist_order in exists_orders[0]:
                        if order_info["posting_number"] == exist_order["posting_number"]:
                            if order_info["cancellation"]["cancel_reason_id"] != exist_order["cancel_reason_id"]:
                                logging.info(f"CANCELED ORDER {order_info['posting_number']}")
                                await change_order(order_info, seller, cancel=True)

                            elif order_info["status"] != exist_order["status"]:
                                await change_order(order_info, seller, status=order_info["status"])

                            break

            except TypeError:

                logging.info(f"ERROR - {TypeError}")

    return


async def change_order(order, seller, new: bool = False, cancel: bool = False, status: str = None):
    in_process_at = await change_dt_api_format(order["in_process_at"], seller["timezone"])
    shipment_date = await change_dt_api_format(order["shipment_date"], seller["timezone"])
    current_time = await get_time(tz=seller["timezone"])
    complete = True

    try:
        await db_query(func='execute',
                       sql="""WITH src AS (INSERT INTO order_info 
                                                   (posting_number, order_id, order_number, warehouse_id, status, 
                                                    address, zip_code, latitude, longitude, 
                                                    customer_id, customer_name, customer_phone, customer_email, 
                                                    customer_comment, addressee_name, addressee_phone, 
                                                    in_process_at, shipment_date, 
                                                    cancel_reason_id, cancel_reason, cancellation_type, 
                                                    cancelled_after_ship, affect_cancellation_rating, 
                                                    cancellation_initiator)
                                      VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 
                                             $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24)
                                      ON CONFLICT (posting_number) DO UPDATE
                                      SET status = $5, customer_comment = $14, cancel_reason_id = $19, 
                                      cancel_reason = $20, cancellation_type = $21, cancelled_after_ship = $22, 
                                      affect_cancellation_rating = $23, cancellation_initiator = $24 RETURNING *)
                                      INSERT INTO logs_status_changes (date, status, status_ozon_seller, posting_number) 
                                      VALUES($25, $5, $5, $1);""",
                       kwargs=[order['posting_number'], order['order_id'], order['order_number'],
                                       order['delivery_method']['warehouse_id'], order["status"],
                                       order['customer']['address']['address_tail'],
                                       order['customer']['address']['zip_code'],
                                       float(order['customer']['address']['latitude']),
                                       float(order['customer']['address']['longitude']),
                                       order['customer']['customer_id'], order['customer']['name'],
                                       order['customer']['phone'], order['customer']['customer_email'],
                                       order['customer']['address']['comment'],
                                       order['addressee']['name'], order['addressee']['phone'],
                                       in_process_at, shipment_date, order['cancellation']['cancel_reason_id'],
                                       order['cancellation']['cancel_reason'],
                                       order['cancellation']['cancellation_type'],
                                       order['cancellation']['cancelled_after_ship'],
                                       order['cancellation']['affect_cancellation_rating'],
                                       order['cancellation']['cancellation_initiator'],
                                       current_time])

        if new:
            for product in order['products']:
                await db_query(func='execute',
                               sql="""INSERT INTO order_list 
                                              (order_id, posting_number, sku, name, offer_id, 
                                               quantity, price, fact_quantity, changed) 
                                              VALUES($1, $2, $3, $4, $5, $6, $7, $6, $8);""",
                               kwargs=[order['order_id'], order['posting_number'], product['sku'],
                                               product['name'], product['offer_id'], product['quantity'],
                                               float(product['price']), False])

    except TypeError:
        logging.info(f"ERROR - {TypeError}")
        complete = False

    finally:
        if new:
            title = fmt.hitalic("Новый заказ")

        elif cancel:
            title = fmt.hitalic("Изменение в заказе")

        else:
            title = ""
            logging.info(f"{order['posting_number']} - {status}")

        if (status is None) and complete:
            await send_info_msg(order, in_process_at, shipment_date, seller, title, current_time)
        return


async def send_info_msg(order, in_process_at, shipment_date, seller, title, current_time):
    last_time = await get_time(0.5, plus=True, tz=seller["timezone"])
    text = fmt.text(
        fmt.text(fmt.hbold("Номер отправления: "), order["posting_number"]),
        fmt.text(fmt.hbold("Статус: "), ORDER_STATE[order["status"]]),
        fmt.text(fmt.hbold("Время создания: "), str(in_process_at)),
        fmt.text(fmt.hbold("Передать курьеру до: "), str(shipment_date)),
        fmt.text(fmt.hbold("Передать клиенту до: "), str(last_time)[:-7]),
        fmt.text(fmt.hbold("Позиций: "), len(order["products"])),
        fmt.text(fmt.hbold("Товаров: "), sum([item["quantity"] for item in order["products"]])),
        fmt.text(fmt.hstrikethrough("-" * 20)),
        fmt.text(fmt.hbold("Отмена: "), order["cancellation"]["cancel_reason_id"]),
        fmt.text(fmt.hbold("Причина отмены: "), order["cancellation"]["cancel_reason"]),
        fmt.text(fmt.hbold("Инициатор отмены: "), order["cancellation"]["cancellation_initiator"]),
        fmt.text(fmt.hstrikethrough("-" * 20)),
        fmt.text(fmt.hbold("Получатель: "), fmt.hitalic(order["addressee"]["name"])),
        fmt.text(fmt.hbold("Тел. получателя: "), fmt.hcode(f"+{order['customer']['phone']}")),
        fmt.text(fmt.hbold("Адрес: "), order["customer"]["address"]["address_tail"]),
        fmt.text(fmt.hstrikethrough("-" * 20)),
        fmt.text(fmt.hbold("Покупатель: "), fmt.hitalic(order["customer"]["name"])),
        fmt.text(fmt.hbold("Тел. покупателя: "), fmt.hcode(f"+{order['customer']['phone']}\n")),
        sep="\n")

    await dp.bot.send_message(chat_id="-701659745" if DEBUG else seller["log_chat_id"],
                              text=fmt.text(title, fmt.hitalic(str(current_time)[:-7]), text, sep="\n\n"))


if __name__ == "__main__":
    pass
