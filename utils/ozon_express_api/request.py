import logging
import requests

from data.config import API_URL, DEBUG, MODER_LOGS
from data.condition import API_METHODS, CANCELLATION_STATUS
from utils.db import sql
from utils.proccess_time import get_time
from utils.message import send_msg


async def check_status(response):
    status = response.status_code
    answer = f'{await get_time()}: Результат запроса API - '
    if status == 200:
        logging.info(answer + 'Получен ответ от сервера')
        return True
    elif status == 400:
        logging.info(answer + 'Неверный параметр')
    elif status == 403:
        logging.info(answer + 'Доступ запрещен')
    elif status == 404:
        logging.info(answer + 'Ответ не найден')
    elif status == 409:
        logging.info(answer + 'Конфликт запроса')
    elif status == 500:
        logging.info(answer + 'Внутренняя ошибка сервера')
    else:
        logging.info(answer + 'Неизвестная ошибка')
    return False


async def post(args, tg_id: int):
    if DEBUG:
        await send_msg(MODER_LOGS, str(args))
        return []
    else:
        api = await sql.get_special_seller_api_info(tg_id)
        response = requests.post(**args, headers={'Client-Id': str(api['seller_id']),
                                                  'Api-Key': api['api_key']})
        if await check_status(response):
            result = response.json()
            return result['result']


async def get_warehouses_list(seller_id, api_key):
    """
    [{'warehouse_id': 22551110574000,
      'name': 'Ozon Express Томск',
      'is_rfbs': True}]
    """
    params = {'url': API_URL + API_METHODS['v1']}
    response = requests.post(**params, headers={'Client-Id': str(seller_id), 'Api-Key': api_key})
    if await check_status(response):
        result = response.json()
        print(result)
        return result['result'][0]['warehouse_id']
    else:
        return None


async def get_info(tg_id: int, sku: int):
    """

    """
    params = {'url': API_URL + API_METHODS['v2'],
              'json': {
                  "offer_id": "",
                  "product_id": 0,
                  "sku": sku}}
    return await post(params, tg_id)


async def get_order_description(tg_id: int, offer_id: str, product_id: int):
    """
    {'id': 173405298,
     'offer_id': 'manl345krhn8egcs79z2',
     'name': 'Вафли Яшкино Голландские, с карамельной начинкой, 290 г',
     'description': 'Песочные вафли с нежной карамельной начинкой.\nГолландскими эти круглые вафли называют неслучайно.
     Считается, что они происходят из города Гауда в Нидерландах, где их впервые на рубеже XVIII-начале XIX века
     произвел некий пекарь. На родине они получили название стропвафли (вафли с патокой).\n– Обычно стропвафли едят,
     как и обычные – вприкуску. Попробуйте другой способ: накройте круглой вафелькой чашку с горячим напитком,
     спустя полминуты она нагреется и станет мягче, вкус станет более бархатистым.'}
    """
    params = {'url': API_URL + API_METHODS['v3'],
              'json': {"offer_id": offer_id,
                       "product_id": product_id}}
    return await post(params, tg_id)


async def get_leftovers_in_stock(tg_id: int):
    """
    {'items': [
        {'product_id': 173405298,
         'offer_id': 'manl345krhn8egcs79z2',
         'stocks': [
         {'type': 'fbo',
          'present': 0,
          'reserved': 0},
         {'type': 'fbs',
          'present': 14,
          'reserved': 0}
         ]
        }
    ]}
    """
    params = {'url': API_URL + API_METHODS['v4'],
              'json': {"page": 2,
                       "page_size": 100}}
    return await post(params, tg_id)


async def get_unfulfilled_list(tg_id: int):
    params = {'url': API_URL + API_METHODS['v5'],
              'json': {"dir": "asc",
                       "filter": {
                           "cutoff_from": (await get_time()).strftime('%Y-%m-%dT%H:%M:%S.91Z'),
                           "cutoff_to": (await get_time(3, plus=True)).strftime('%Y-%m-%dT%H:%M:%S.91Z')},
                       "limit": 1000,
                       "offset": 0}}
    return await post(params, tg_id)


async def get_orders_list(tg_id: int):
    params = {'url': API_URL + API_METHODS['v6'],
              'json': {"dir": "ASC",
                       "filter": {
                           "since": (await get_time(720, minus=True)).strftime('%Y-%m-%dT%H:%M:%S.00Z'),
                           "to": (await get_time()).strftime('%Y-%m-%dT%H:%M:%S.00Z')},
                       "limit": 100,
                       "offset": 0}}
    return await post(params, tg_id)


async def cancel_order(posting_number: str, tg_id: int, cancel_reason_id: int, cancel_msg: str = None):
    param = {'url': API_URL + API_METHODS['v13'],
             'json': {"cancel_reason_id": cancel_reason_id,
                      "cancel_reason_message": cancel_msg if cancel_msg else CANCELLATION_STATUS[cancel_reason_id],
                      "posting_number": posting_number}}
    return await post(param, tg_id)


async def delete_products(params, tg_id):
    param = {'url': API_URL + API_METHODS['v14'],
             'json': params}
    return await post(param, tg_id)


async def complete_packaging_ozon_old(products, tg_id):
    posting_number = products[0]["posting_number"]
    params = {'url': API_URL + API_METHODS['v8'],
              'json': {"posting_number": posting_number,
                       "products": []}}
    count = 0
    for product in products:
        if product["fact_quantity"] - product["quantity"] != 0:
            count += 1
        params['json']["products"].append({"product_id": product["sku"],
                                           "quantity": product["fact_quantity"]})
    new_posting_number = await post(params, tg_id)

    status = await cancel_order(posting_number, tg_id, 352) if count != 0 else False
    return new_posting_number, status, posting_number


async def complete_packaging_ozon(products, tg_id):
    posting_number = products[0]["posting_number"]

    param = {'url': API_URL + API_METHODS['v8'],
             'json': {"posting_number": posting_number,
                      "products": []}}

    param_for_cancel = {"cancel_reason_id": 352,
                        "cancel_reason_message": "Product is out of stock",
                        "items": [],
                        "posting_number": posting_number}

    count = 0
    for product in products:
        if product["quantity"] - product["fact_quantity"] == product["quantity"]:
            param_for_cancel["items"].append({"quantity": product["quantity"],
                                              "sku": product["sku"]})
        elif product["quantity"] - product["fact_quantity"] != 0:
            count += 1
            param_for_cancel["items"].append({"quantity": product["quantity"] - product["fact_quantity"],
                                              "sku": product["sku"]})
            param['json']["products"].append({"product_id": product["sku"],
                                              "quantity": product["fact_quantity"]})
        else:
            count += 1
            param['json']["products"].append({"product_id": product["sku"],
                                              "quantity": product["fact_quantity"]})

    cancel_status = await cancel_order(posting_number, tg_id, 352) if count == 0 else False

    if param_for_cancel["items"]:
        status = await delete_products(param_for_cancel, tg_id)
        if status:
            logging.info('Товар успешно убран из заказа')
    else:
        status = False

    await send_weight(posting_number, tg_id, products)

    await post(param, tg_id) if count != 0 else False

    return status, cancel_status, posting_number


async def start_delivery_api(tg_id, posting_numbers):
    param = {'url': API_URL + API_METHODS['v9'],
             'json': {'posting_number': posting_numbers}}
    return await post(param, tg_id)


async def start_delivery_last_mile(tg_id, posting_numbers):
    param = {'url': API_URL + API_METHODS['v11'],
             'json': {'posting_number': posting_numbers}}
    return await post(param, tg_id)


async def complete_delivery_ozon(tg_id, posting_number):
    param = {'url': API_URL + API_METHODS['v12'],
             'json': {'posting_number': [posting_number]}}
    return await post(param, tg_id)


async def send_weight(posting_number: str, tg_id: int, products: list):
    items = []
    for product in products:
        if product["weight"]:
            items.append({"quantity": product["fact_quantity"],
                          "sku": product["sku"],
                          "weightAdjust": True,
                          "weightReal": [product["weight"] / 1000]})
    param = {'url': API_URL + API_METHODS['v16'],
             'json': {"items": items,
                      'posting_number': [posting_number]}}
    return await post(param, tg_id)


if __name__ == '__main__':
    pass
