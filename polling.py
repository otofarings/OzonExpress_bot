import asyncio

from aiogram.utils.exceptions import MessageNotModified
from aiohttp import ClientSession, ClientResponse
from aiohttp.client_exceptions import ContentTypeError, ServerDisconnectedError, ClientResponseError, \
    ClientConnectorError, ClientConnectionError

from data.config import DEBUG, TIMEOUT_POLLING, TIMEOUT_SMALL_ERROR, TIMEOUT_BIG_ERROR
from utils.db import sql
from utils.misc.debug import get_orders_from_local
from utils.formate_text import order_description, get_new_title, cancel_description, edit_description
from utils.message import cancel_action_message, alert_seller_logs, send_msg, edit_order_msg, alert_logs
from utils.ozon_express_api.request import get_orders_list_query, check_status, get_info
from utils.proccess_time import check_error_time, get_diff, get_dt_for_polling
from data.output_console_logs import logging_info, logging_error


class Order:
    def __init__(self, order_info: dict, seller_name: str, seller_id: str, warehouse_id: int, api_key: str,
                 log_chat_id: str, channel_id: str, timezone: str, exists_orders_: list):
        self.info = order_info
        self.posting_number = order_info["posting_number"]
        self.order_number = order_info["order_number"]
        self.products_info = {}
        self.tags = []

        self.seller_name = seller_name
        self.seller_id = seller_id

        self.warehouse_id = warehouse_id
        self.api_key = api_key

        self.log_chat_id = log_chat_id
        self.channel_id = channel_id

        self.timezone = timezone
        self.dt_obj = None

        self.exists_orders = exists_orders_
        self.exists_orders_numbers = []
        self.exists_posting_numbers = []
        self.exist_order = None
        self.exist_post = None

        self.updating_action = None

    async def check_order_in_exist(self):
        self.exists_orders_numbers = [order["order_number"] for order in self.exists_orders]
        self.exists_posting_numbers = [order["posting_number"] for order in self.exists_orders]
        self.exist_order = await self.search_in_exists(self.order_number, self.exists_orders_numbers)
        self.exist_post = await self.search_in_exists(self.posting_number, self.exists_posting_numbers)

        self.dt_obj = await get_dt_for_polling(self.info["in_process_at"], self.info["shipment_date"], self.timezone)

    async def search_in_exists(self, arg_, posts_) -> dict:
        return self.exists_orders[posts_.index(arg_)] if arg_ in posts_ else None

    async def try_process_order(self):
        try:
            await self.check_order_in_exist()
            await self.get_action_function()

            if self.updating_action:
                await self.updating_action()
            else:
                await self.update_description()

        except MessageNotModified:
            pass

        except TypeError:
            if self.info['posting_number']:
                await logging_error(f"ERROR - Getting order - {self.posting_number}")
                # await alert_logs("13")
                await sql.write_error_log(error_name=str(TypeError), tz=self.timezone, error_type="TypeError",
                                          warehouse_id=self.warehouse_id, posting_number=self.posting_number)
                await self.alert_about_error()

    async def get_action_function(self):
        if not self.exist_post:
            self.updating_action = self.update_partial_cancel_status if self.exist_order else self.create_new_posting
        else:
            if self.info["cancellation"]["cancel_reason_id"] != self.exist_post["cancel_reason_id"]:
                self.updating_action = self.update_cancel_status
            elif self.info["status"] != self.exist_post["status_api"]:
                self.updating_action = self.update_status_api
        return

    async def alert_about_error(self):
        error_info = await sql.get_first_time_error(self.posting_number, self.warehouse_id)
        if await check_error_time(error_info, self.timezone):
            await alert_seller_logs(self.posting_number, self.log_chat_id)
        await asyncio.sleep(TIMEOUT_BIG_ERROR)

    async def check_relevance(self):
        if self.exist_post["status"] not in ["delivered", "conditionally_delivered", "cancelled"]:
            return True
        return False

    async def create_new_posting(self):
        await logging_info(f"NEW ORDER {self.posting_number}")
        await self.write_order_info_to_db()
        await self.get_product_rank()
        await sql.create_new_products(self.info, self.products_info)
        self.tags = [str(self.dt_obj["current_time"])[:11].replace("-", "")]
        await self.write_hashtags(self.tags)
        title = await get_new_title(self.info["status"])
        await self.write_title(title)
        text = await order_description(self.info, self.dt_obj["in_process_at"], self.dt_obj["shipment_date"],
                                       self.dt_obj["predicted_date"], self.tags, title_=title)
        info = await send_msg(self.channel_id, text)
        await sql.insert_order_message_id(self.posting_number, info["message_id"], self.channel_id)

    async def update_cancel_status(self):
        await logging_info(f"CANCELED ORDER {self.posting_number}")
        await self.write_order_info_to_db()
        await cancel_action_message(self.posting_number)
        title = await get_new_title()
        await self.write_title(title)
        await self.change_status()
        await sql.write_tag(self.order_number, self.timezone, "отменен")
        hashtags = await sql.get_tags(self.order_number)

        text = await order_description(self.info, self.dt_obj["in_process_at"], self.dt_obj["shipment_date"],
                                       self.dt_obj["predicted_date"], hashtags, title_=title)
        await self.write_msg(text)

        cancel_text = await cancel_description(self.info, title)
        msg_id_reply = await sql.get_order_msg_id(order_number=self.order_number)
        await send_msg(self.log_chat_id, cancel_text, msg_id_reply)
        return

    async def update_partial_cancel_status(self):
        await logging_info(f"PART-CANCELED ORDER {self.posting_number}")
        await self.write_order_info_to_db()
        await sql.create_part_cancelled_products(self.info)
        title = await get_new_title(self.info["status"])
        await self.write_title(title)
        await sql.write_tag(self.order_number, self.timezone, "частично_отменен")
        hashtags = await sql.get_tags(self.order_number)

        main_posting = await sql.get_order_info(self.exist_order["posting_number"])
        self.dt_obj = await get_dt_for_polling(main_posting["in_process_at"], main_posting["shipment_date"],
                                               self.timezone)

        text = await edit_description(title, dict(main_posting), self.dt_obj["predicted_date"], hashtags)
        await self.write_msg(text)

        cancel_text = await cancel_description(self.info, title)
        msg_id_reply = await sql.get_order_msg_id(order_number=self.order_number)
        await send_msg(self.log_chat_id, cancel_text, msg_id_reply)
        return

    async def update_status_api(self):
        await logging_info(f"UPDATE STATUS API {self.posting_number} -> {self.info['status']}")
        await self.write_order_info_to_db()

        if self.info["status"] in ["delivered", "cancelled"]:
            title = "📌Завершен" if self.info["status"] == "delivered" else "📌Отменен"
            if title != self.exist_post["current_status"]:
                await self.write_title(title)
                await self.change_status()
                await self.write_hashtags(["завершен" if self.info["status"] == "delivered" else "отменен"])
                self.tags = await sql.get_tags(self.order_number)
                text = await order_description(
                    self.info, self.dt_obj["in_process_at"], self.dt_obj["shipment_date"],
                    self.dt_obj["predicted_date"], self.tags, title_=title,
                    status_=self.info["status"])
                await self.write_msg(text)

        elif (self.info["status"] == "delivering") and (self.exist_post["status"] == "delivering"):
            await self.change_status()
            await self.update_description()

        elif await self.condition_to_change_status():
            title = "⚠️Статус переведен из ЛK"
            if title != self.exist_post["current_status"]:
                await self.write_title(title)
                await self.change_status()
                await self.write_hashtags(["изменен_в_лк"])
                self.tags = await sql.get_tags(self.order_number)
                text = await order_description(
                    self.info, self.dt_obj["in_process_at"], self.dt_obj["shipment_date"],
                    self.dt_obj["predicted_date"], self.tags)
                await self.write_msg(text)
        return

    async def condition_to_change_status(self):
        if ((self.info["status"] == "delivering") and (
                (self.exist_post["status"] not in [
                    "delivered", "undelivered", "conditionally_delivered", "cancelled", "reserved_by_deliver"])
                or (not self.exist_post["start_delivery_date"]))):
            return True
        return False

    async def update_description(self):
        title, new_hashtag = await self.edit_exist_post()
        if title:
            if title != self.exist_post["current_status"]:
                await self.write_title(title)

                hashtags = await sql.get_tags(self.order_number)
                if new_hashtag:
                    if new_hashtag not in hashtags:
                        hashtags.append(new_hashtag)
                        await sql.write_tag(self.order_number, self.timezone, new_hashtag)

                text = await order_description(self.info, self.dt_obj["in_process_at"], self.dt_obj["shipment_date"],
                                               self.dt_obj["predicted_date"], hashtags, status_=self.info["status"],
                                               title_=title)
                await self.write_msg(text)
        return

    async def write_order_info_to_db(self):
        await sql.create_new_order(self.info, self.dt_obj["in_process_at"],
                                   self.dt_obj["shipment_date"], self.dt_obj["current_time"])

    async def change_status(self) -> str:
        return await sql.update_order_last_status(self.info["status"], self.posting_number, self.timezone)

    async def write_hashtags(self, tags_: list):
        for tag in tags_:
            if tag not in self.tags:
                await sql.write_tag(self.order_number, self.timezone, tag)

    async def write_title(self, title_):
        await sql.write_current_status(self.posting_number, title_)

    async def write_msg(self, text_):
        try:
            await edit_order_msg(self.info, self.channel_id, text_)
        except MessageNotModified:
            return True

    async def get_product_rank(self):
        for product in self.info['products']:
            info_ = await get_info(product['sku'], seller_id=str(self.seller_id), api_key=self.api_key)
            self.products_info[str(product['sku'])] = {}
            if info_:
                for key, value in info_.items():
                    if key in ['id', 'name', 'barcode', 'category_id', 'price', 'volume_weight', 'primary_image']:
                        if key == "id":
                            self.products_info[str(product['sku'])]["product_id"] = value
                        else:
                            self.products_info[str(product['sku'])][key] = value
                        if key == 'category_id':
                            self.products_info[str(product['sku'])]['rank'] = await sql.get_product_rank(value)

    async def edit_exist_post(self):
        hashtag = None
        time_left = await get_diff(self.timezone, self.dt_obj["shipment_date"])
        title = None
        if self.exist_post["status"] in ["awaiting_packaging", "reserved_by_packer"]:
            if time_left <= 2:
                title = "❕Нужно взять заказ в сборку"
            elif time_left > 2:
                title = "❗Нужно начать собирать"
            elif time_left > 30:
                title = "☠️Заказ просрочен"
                hashtag = "просрочен"

        elif self.exist_post["status"] == "packaging":
            if time_left <= 5:
                title = "📦Собирается"
            elif 5 < time_left <= 6:
                title = "🕙Осталась 1 минута для завершения сборки"
            elif time_left > 6:
                title = "❗️Нужно передать заказ в доставку"
            elif time_left > 30:
                title = "☠️Заказ просрочен"
                hashtag = "сборка_просрочена"

        elif self.exist_post["status"] in ["awaiting_deliver", "reserved_by_deliver"]:
            if time_left <= 11:
                title = "❕Нужно взять заказ в доставку"
            elif 11 < time_left < 30:
                title = "❗️Нужно начать доставлять"
            elif time_left > 30:
                title = "☠️Заказ просрочен"
                hashtag = "доставка_просрочена"

        elif self.exist_post["status"] == "delivering":
            if time_left < 25:
                title = "🛺Доставляется"
            if time_left == 25:
                title = "🕙Осталось 5 минут до завершения доставки"
            elif time_left > 30:
                title = "⚠️Доставка опаздывает"
                hashtag = "доставка_опаздывает"

        elif self.exist_post["status"] == "conditionally_delivered":
            title = "📍Условно доставлен"

        return title, hashtag


class SellerOzonAPI:
    def __init__(self, seller_info):
        self.seller_name = seller_info["seller_name"]
        self.seller_id = seller_info["seller_id"]

        self.warehouse_id = seller_info["warehouse_id"]
        self.api_key = seller_info["api_key"]

        self.log_chat_id = seller_info["log_chat_id"]
        self.channel_id = seller_info["channel_id"]

        self.timezone = seller_info["timezone"]

        self.new_response = []

    async def start(self):
        try:
            asyncio.create_task(self.get_webhook())

        except Exception as error:
            await logging_error(error)
            await sql.write_error_log(error_name=str(error), error_type="Exception")

        finally:
            await logging_info(f'Выход из процесса опроса API для {self.seller_name}')

    async def get_webhook(self):
        while True:
            try:
                await self.create_poll()
                await asyncio.sleep(TIMEOUT_POLLING)

            except asyncio.CancelledError:
                await sql.write_error_log(error_name=str(asyncio.CancelledError), error_type="CancelledError")
                return False

            except ConnectionError:
                await logging_error(f"Ошибка соединения {ConnectionError}")
                await sql.write_error_log(error_name=str(ConnectionError), error_type="ConnectionError")
                await asyncio.sleep(TIMEOUT_BIG_ERROR)

            except ContentTypeError:
                await logging_error("Ошибка в типе полученного контента", ContentTypeError)
                await alert_logs("12")
                await sql.write_error_log(error_name=str(ContentTypeError), error_type="ContentTypeError")
                await asyncio.sleep(TIMEOUT_SMALL_ERROR)

    async def create_poll(self):
        if not DEBUG:
            self.new_response = await self.get_api_response()
        else:
            self.new_response = await get_orders_from_local()

        if self.new_response:
            await self.process_response()
        return

    async def get_api_response(self):
        try:
            async with ClientSession() as session:
                return await self.get_response(session)

        except ServerDisconnectedError:
            await logging_error("Отключение от сервера запроса", str(ServerDisconnectedError))
            await alert_logs("6")
            await sql.write_error_log(error_name=str(ServerDisconnectedError), tz=self.timezone,
                                      error_type="ServerDisconnectedError", warehouse_id=self.warehouse_id)
            await asyncio.sleep(TIMEOUT_BIG_ERROR)

        except ClientResponseError:
            await logging_error("Ошибка запроса", str(ClientResponseError))
            await alert_logs("7")
            await sql.write_error_log(error_name=str(ClientResponseError), tz=self.timezone,
                                      error_type="ClientResponseError", warehouse_id=self.warehouse_id)
            await asyncio.sleep(TIMEOUT_BIG_ERROR)

        except ClientConnectorError:
            await logging_error("Ошибка подключения", str(ClientConnectorError))
            await alert_logs("8")
            await sql.write_error_log(error_name=str(ClientConnectorError), tz=self.timezone,
                                      error_type="ClientConnectorError", warehouse_id=self.warehouse_id)
            await asyncio.sleep(TIMEOUT_BIG_ERROR)

        except ClientConnectionError:
            await asyncio.sleep(TIMEOUT_BIG_ERROR)

    async def get_response(self, session):
        try:
            async with session.post(**await get_orders_list_query(seller_id_=str(self.seller_id),
                                                                  api_key_=self.api_key)) as response:
                return await self.check_response(response)

        except TimeoutError:
            await logging_error("Превышено время ожидания ответа", str(TimeoutError))
            await alert_logs("4")
            await sql.write_error_log(error_name=str(TimeoutError), tz=self.timezone,
                                      error_type="TimeoutError", warehouse_id=self.warehouse_id)
            await asyncio.sleep(TIMEOUT_BIG_ERROR)

        except ValueError:
            await logging_error("Ошибка значения", str(ValueError))
            await alert_logs("5")
            await sql.write_error_log(error_name=str(ValueError), tz=self.timezone,
                                      error_type="ValueError", warehouse_id=self.warehouse_id)
            await asyncio.sleep(TIMEOUT_BIG_ERROR)

    async def check_response(self, response):
        result = []
        try:
            if await check_status(response, self.timezone, self.warehouse_id):
                result_json = await response.json()
                result = result_json["result"]["postings"] if result_json else []

        except ContentTypeError:
            await logging_error("Ошибка типа данных", ContentTypeError)
            await sql.write_error_log(error_name=str(ContentTypeError), tz=self.timezone,
                                      error_type="ContentTypeError", warehouse_id=self.warehouse_id)
            result = []

        finally:
            return result

    async def process_response(self):
        if DEBUG:
            await logging_info(len(self.new_response))

        exists_orders = await sql.get_orders_info_for_polling(self.warehouse_id)
        for order_info in self.new_response:
            await Order(order_info, self.seller_name, self.seller_id, self.warehouse_id, self.api_key,
                        self.log_chat_id, self.channel_id, self.timezone, exists_orders).try_process_order()
        return


async def start_polling_api():
    try:
        await logging_info('Старт опроса API')
        asyncio.create_task(main())

    except Exception as error:
        await logging_error(error)
        await alert_logs("9")
        await sql.write_error_log(error_name=str(error), error_type="Exception")


async def main():
    for seller in await sql.get_sellers_api_info():
        await SellerOzonAPI(seller).start()


async def check_error(function_, *args):
    try:
        return await function_(*args)
    except (ContentTypeError, ServerDisconnectedError, ClientResponseError, ClientConnectorError,
            ClientSession, ClientResponse, TypeError, ConnectionError) as err:
        await logging_error(f"ERROR -  {err}")
        return None


if __name__ == "__main__":
    pass
