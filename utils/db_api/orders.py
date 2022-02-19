import math

from data.config import MAX_DISTANCE
from data.condition import CANCELLATION_STATUS
from utils.db_api.database import db_query
from utils.proccess_time import get_time


async def get_quantity_of_orders(tg_id: int, status: str):
    orders = await db_query(action='fetch', sql_com='get_quantity_of_orders',
                            kwarg=[tg_id, status])

    return orders[0][0]["count"]


async def get_exists_orders(warehouse_id):
    orders = await db_query(action='fetch', sql_com='get_all_orders',
                            kwarg=[warehouse_id])

    return orders[0]


# ****************************************Package****************************************
async def reserve_package(tg_id: int, reserve: bool = False, posting_number: str = None):
    if reserve:
        if posting_number:
            await db_query(action='execute', sql_com='reserve_order_by_admin',
                           kwarg=[posting_number, 'reserved_by_packer', tg_id, 'awaiting_packaging'])
        else:
            orders = await db_query(action='fetch', sql_com='orders_reserve_package',
                                    kwarg=[tg_id, 'awaiting_packaging', 'reserved_by_packer'])

            return orders[0]

    else:
        return await db_query(action='fetch', sql_com='remove_reserve_orders_for_packaging',
                              kwarg=[tg_id, 'reserved_by_packer', 'awaiting_packaging', None])


async def start_packaging(tg_id: int, posting_number: str, tz: str):
    await db_query(action='execute', sql_com='start_packaging',
                   kwarg=[posting_number, 'reserved_by_packer', "packaging",
                          'awaiting_packaging', tg_id, None, (await get_time(tz=tz)).replace(tzinfo=None)])

    return


async def get_order_list(posting_number):
    orders = await db_query(action='fetch', sql_com='get_order_list',
                            kwarg=[posting_number])

    return orders[0]


async def update_order_list(name, quantity, posting_number):
    await db_query(action='execute', sql_com='update_order_list', kwarg=[name, quantity, posting_number])
    return


async def complete_packaging(posting_number: str, tz: str, cancel: bool = False):
    if cancel:
        await cancel_order(posting_number, 352, tz)
    else:
        await db_query('execute', 'complete_packaging',
                       kwarg=[posting_number, 'awaiting_deliver', (await get_time(tz=tz)).replace(tzinfo=None),
                              'awaiting_deliver'])
    return


async def cancel_order(posting_number: str, cancel_reason_id: int, tz: str):
    await db_query("execute", "cancel_packaging", kwarg=[posting_number, "canceled",
                                                         (await get_time(tz=tz)).replace(tzinfo=None),
                                                         "canceled", cancel_reason_id,
                                                         CANCELLATION_STATUS[cancel_reason_id], "seller", "Продавец"])


# ****************************************Delivery****************************************
async def reserve_for_delivery(tg_id: int, reserve: bool = False):
    if reserve:
        orders = await db_query(action='fetch', sql_com='orders_awaiting_delivery',
                                kwarg=[tg_id, 'awaiting_deliver'])

        sorted_orders = await get_similar_orders(orders[0][0], orders[0])

        final_orders = await db_query(action='fetch', sql_com='orders_reserve_delivery',
                                      kwarg=[tuple([order['posting_number'] for order in sorted_orders]),
                                             tg_id, 'reserved_by_deliver'])

        return final_orders[0]

    else:
        return await db_query(action='fetch', sql_com='remove_reserve_orders_for_delivering',
                              kwarg=[tg_id, 'reserved_by_deliver', 'awaiting_deliver', None])


async def get_info_reserved_orders(posting_number: str):
    orders = await db_query(action='fetch', sql_com='get_info_reserved_for_delivering',
                            kwarg=[posting_number, 'reserved_by_deliver'])

    return orders[0][0]


async def get_similar_orders(mandatory_order, ex_orders):
    """
    Получаем заказы, которые находятся недалеко от основного, если такие есть
    """
    orders = [mandatory_order]
    if len(ex_orders) > 1:
        count = 0
        for ex_order in ex_orders:
            distance = await calculate_distance(mandatory_order['latitude'], mandatory_order['longitude'],
                                                ex_order['latitude'], ex_order['longitude'])
            if (distance <= MAX_DISTANCE) and (mandatory_order['posting_number'] != ex_order['posting_number']):
                orders.append(ex_order)
                count += 1
            if count == 9:
                break
    return orders


async def calculate_distance(lat1_, lon1_, lat2_, lon2_):
    """
    Функция для расчета растояния между двумя точками по широте и долготе (Формула Haversine)
    """
    radius = 6373.0  # Радиус земли
    lat1, lon1, lat2, lon2 = math.radians(lat1_), math.radians(lon1_), math.radians(lat2_), math.radians(lon2_)
    d_lon, d_lat = lon2 - lon1, lat2 - lat1
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return (radius * c) * 1000


async def start_delivery(orders: tuple, tg_id: int, tz: str):
    orders = await db_query(action='fetch', sql_com='start_delivering',
                            kwarg=[orders, tg_id, 'delivering', (await get_time(tz=tz)).replace(tzinfo=None)])

    return orders[0]


async def finish_order_delivery(posting_number: str, tz: str, cancel_reason: str = None):
    if cancel_reason:
        status, successfully, ozon_status = 'undelivered', False, 'delivering'
    else:
        status, successfully, ozon_status = 'delivered', True, 'delivered'
    await db_query(action='execute', sql_com='complete_delivery',
                   kwarg=[posting_number, status, (await get_time(tz=tz)).replace(tzinfo=None), ozon_status])
# ********************************************************************************


async def get_orders_for_polling(seller_id, tz):
    time = await get_time(24, minus=True, tz=tz)
    orders = await db_query(action='fetch', sql_com='get_orders_for_polling',
                            kwarg=[seller_id, time.replace(tzinfo=None)])
    return orders


async def create_new_products(order):
    for product in order['products']:
        await db_query(action='execute', sql_com='new_products',
                       kwarg=[order['order_id'],
                              order['posting_number'],
                              product['sku'],
                              product['name'],
                              product['offer_id'],
                              product['quantity'],
                              float(product['price']),
                              False])


async def create_new_order(order, in_process_at, shipment_date, current_time):
    try:
        await db_query(action='execute', sql_com='new_order',
                       kwarg=[order['posting_number'],
                              order['order_id'],
                              order['order_number'],
                              order['delivery_method']['warehouse_id'],
                              order["status"],
                              order['customer']['address']['address_tail'],
                              order['customer']['address']['zip_code'],
                              float(order['customer']['address']['latitude']),
                              float(order['customer']['address']['longitude']),
                              order['customer']['customer_id'],
                              order['customer']['name'],
                              order['customer']['phone'],
                              order['customer']['customer_email'],
                              order['customer']['address']['comment'],
                              order['addressee']['name'],
                              order['addressee']['phone'],
                              in_process_at,
                              shipment_date,
                              order['cancellation']['cancel_reason_id'],
                              order['cancellation']['cancel_reason'],
                              order['cancellation']['cancellation_type'],
                              order['cancellation']['cancelled_after_ship'],
                              order['cancellation']['affect_cancellation_rating'],
                              order['cancellation']['cancellation_initiator'],
                              current_time])
    except TypeError:
        pass
    finally:
        return


async def update_order(posting_number, status, cancel_reason_id):
    await db_query(action='execute', sql_com='update_order',
                   kwarg=[posting_number, status, cancel_reason_id])
    return


async def get_orders(seller_id: int = None, tg_id: int = None, posting_number: str = None, status: str = None,
                     orders: tuple = None, package: bool = False, deliver: bool = False, count: bool = False,
                     reserve: bool = False, remove: bool = False, get: bool = False, finish: bool = False,
                     cancel_reason: str = None, order_list: bool = False, quantity: bool = False,
                     delete: bool = False, reset: bool = False, update: bool = False, name: str = None):
    if update:
        sql_com, kwarg, action = 'update_order_list', [name, quantity, posting_number], 'execute'
    elif finish:
        if cancel_reason:
            status, successfully = 'undelivered', False
        else:
            status, successfully = 'delivered', True
        ozon_status = '-n'
        kwarg = [posting_number, status, await get_time(), successfully, cancel_reason, ozon_status]
        sql_com, action = 'complete_delivery', 'execute'
    elif orders:
        sql_com, kwarg, action = 'start_delivering', [orders, tg_id, 'delivering', await get_time()], 'fetch'
    elif package:
        sql_com = 'get_orders_for_delivering' if count else 'get_orders_for_packaging'
        kwarg, action = [tg_id, 'awaiting_packaging'], 'fetch'
    elif deliver:
        sql_com = 'get_orders_for_delivering' if count else ''
        kwarg, action = [tg_id, 'awaiting_delivering'], 'fetch'
    elif seller_id:
        sql_com, kwarg, action = 'get_orders', [seller_id, status, await get_time(24, minus=True)], 'fetch'
    elif tg_id:
        if reserve:
            sql_com, kwarg = 'get_orders_and_reserved_for_delivering', [tg_id, 'awaiting_delivering',
                                                                        'reserved_by_deliver']
        elif remove:
            sql_com, kwarg = 'remove_reserve_orders_for_delivering', [tg_id, 'reserved_by_deliver',
                                                                      'awaiting_delivering', None]
        else:
            sql_com, kwarg = 'get_orders_by_tg_id', [tg_id, await get_time(24, minus=True)]
        action = 'fetch'
    elif posting_number:
        if get:
            sql_com, kwarg = 'get_reserved_for_delivering', [posting_number, 'reserved_by_deliver']
        elif quantity:
            sql_com, kwarg = 'get_order_quantity', [posting_number]
        else:
            sql_com, kwarg = 'get_order_list' if order_list else 'get_order_info', [posting_number]
        action = 'fetch'
        if delete:
            sql_com, kwarg, action = 'delete_order', [posting_number], 'execute'
        elif reset:
            sql_com, kwarg, action = 'reset_order', [posting_number, 'awaiting_packaging',
                                                     None, None, None, None, None, None, None, None], 'execute'
    else:
        sql_com, kwarg, action = '', [], ''

    orders = await db_query(action=action, sql_com=sql_com, kwarg=kwarg)
    return orders[0] if action == 'fetch' else ''


async def get_orders_info(tz: str = 'Europe/Moscow', seller_id: int = None, status: str = None,
                          posting_number: str = None, tg_id: int = None):
    time = await get_time(24, minus=True, tz=tz)

    if posting_number:
        orders = await db_query(action='fetch', sql_com='get_order_info',
                                kwarg=[posting_number])
    elif seller_id:
        orders = await db_query(action='fetch', sql_com='get_orders',
                                kwarg=[seller_id, status, time.replace(tzinfo=None)])
    elif tg_id:
        orders = await db_query(action='fetch', sql_com='get_orders_by_tg_id',
                                kwarg=[tg_id, time.replace(tzinfo=None)])
    else:
        orders = ['']

    return orders[0]


async def reassign(posting_number: str, new_user_id: int):
    sql_com, action = 'reassign_packer_order', 'execute'
    kwarg = [posting_number, new_user_id, await get_time()]
    await db_query(action=action, sql_com=sql_com, kwarg=kwarg)

