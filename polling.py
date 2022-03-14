import aiohttp
from aiohttp.client_exceptions import ContentTypeError, ServerDisconnectedError, ClientResponseError, \
    ClientConnectorError
import asyncio
import aiogram.utils.markdown as fmt
import logging

from loader import dp
from utils.db import sql
from data.condition import ORDER_STATUS_API, API_METHODS
from data.config import API_URL, USER_AGENT, DEBUG
from utils.message import cancel_action_message
from utils.proccess_time import get_time, change_dt_api_format, get_predict_time_for_delivery


async def start_polling_api():
    if not DEBUG:
        try:
            logging.info('Старт опроса API')
            asyncio.create_task(main())

        except Exception as e:
            print(e)


async def main():
    while True:
        await asyncio.sleep(5)

        try:
            for seller in await sql.get_seller_api_info():
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
                await asyncio.sleep(15)

    except (ServerDisconnectedError, ClientResponseError, ClientConnectorError) as error_2:
        logging.error(error_2)
        await asyncio.sleep(15)


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
        exists_orders = await sql.get_orders_info_for_polling(seller["warehouse_id"])

        for order_info in response:
            try:
                if order_info["posting_number"] not in [order["posting_number"] for order in exists_orders]:
                    logging.info(f"NEW ORDER {order_info['posting_number']}")
                    await change_order(order_info, seller, new=True)

                else:
                    for exist_order in exists_orders:
                        if order_info["posting_number"] == exist_order["posting_number"]:
                            if order_info["cancellation"]["cancel_reason_id"] != exist_order["cancel_reason_id"]:
                                logging.info(f"CANCELED ORDER {order_info['posting_number']}")
                                await sql.update_order_last_status(order_info["status"],
                                                                   order_info['posting_number'],
                                                                   seller["timezone"])
                                await change_order(order_info, seller, cancel=True)

                            elif order_info["status"] != exist_order["status_api"]:
                                if order_info["status"] in ["delivered", "cancelled"]:
                                    await sql.update_order_last_status(order_info["status"],
                                                                       order_info['posting_number'],
                                                                       seller["timezone"])

                                await change_order(order_info, seller, status=order_info["status"])

                            elif order_info["status"] != exist_order["status"]:
                                if order_info["status"] in ["delivered", "cancelled"]:
                                    await sql.update_order_last_status(order_info["status"],
                                                                       order_info['posting_number'],
                                                                       seller["timezone"])

                            break

            except TypeError as e:
                logging.info(f"ERROR - {e}")

    return


async def change_order(order, seller, new: bool = False, cancel: bool = False, status: str = None):
    in_process_at = await change_dt_api_format(order["in_process_at"], seller["timezone"])
    shipment_date = await change_dt_api_format(order["shipment_date"], seller["timezone"])
    current_time = await get_time(tz=seller["timezone"])
    complete = True

    try:
        await sql.create_new_order(order, in_process_at, shipment_date, current_time)

        if new:
            await sql.create_new_products(order)

    except TypeError:
        logging.info(f"ERROR - {TypeError}")
        complete = False

    finally:
        if new:
            title = fmt.hitalic("Новый заказ")

        elif cancel:
            title = fmt.hitalic("❗Изменение в заказе❗")
            await cancel_action_message(order['posting_number'])

        else:
            title = ""
            logging.info(f"{order['posting_number']} - {status}")

        if (status is None) and complete:
            await send_info_msg(order, in_process_at, shipment_date, seller, title, current_time)
        return


async def send_info_msg(order, in_process_at, shipment_date, seller, title, current_time):
    complete_time = await get_predict_time_for_delivery(shipment_date, 24)
    text = fmt.text(
        fmt.text(fmt.hbold("Номер отправления: "), order["posting_number"]),
        fmt.text(fmt.hbold("Статус: "), ORDER_STATUS_API[order["status"]]),
        fmt.text(fmt.hbold("Время создания: "), str(in_process_at)),
        fmt.text(fmt.hbold("Передать курьеру до: "), str(shipment_date)),
        fmt.text(fmt.hbold("Передать клиенту до: "), str(complete_time)),
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
        fmt.text(fmt.hbold("Коментарий: "), order['customer']['address']['comment']),
        sep="\n")

    await dp.bot.send_message(chat_id="-701659745" if DEBUG else seller["log_chat_id"],
                              text=fmt.text(title, fmt.hitalic(str(current_time)[:-7]), text, sep="\n\n"))


if __name__ == "__main__":
    pass
