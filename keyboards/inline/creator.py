from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from data.condition import ORDER_STATUS
from utils.formate_button import create_reply_markup, CreatorButton
from utils.formate_text import CreatorMenu
from utils.db.orders import get_orders_info
from utils.db import sql

creator_btn = CreatorButton()
creator_txt = CreatorMenu()
callback_data = CallbackData('creator', 'menu', 'level', 'seller', 'option', 'item', 'item_id', 'action')


async def create_button(text: str, args: list):
    return InlineKeyboardButton(text=text, callback_data=callback_data.new(*args))


async def get_level_1(function: str, status: str):
    return await create_reply_markup(await creator_txt.create_menu_1(),
                                     await creator_btn.buttons_1(function))


async def get_bot_level_2(function: str):
    return await create_reply_markup(await creator_txt.create_menu_2_1(),
                                     await creator_btn.buttons_2_1(function))


async def get_bot_level_3(function: str, callback=None):
    if callback:
        if callback['action'] == 'delete':
            await sql.deactivate_api(callback['item'])
        elif callback['action'] == 'reactive':
            await sql.activate_api(callback['item'])

    sellers_api = await sql.get_all_api_info()

    return await create_reply_markup(await creator_txt.create_menu_3_1(len(sellers_api)),
                                     await creator_btn.buttons_3_1(function, sellers_api))


async def get_bot_level_4(function: str, callback):
    return await create_reply_markup(await creator_txt.create_menu_4_1(callback['item'], callback['seller']),
                                     await creator_btn.buttons_4_1(function, callback['item'],
                                                                   callback['seller'], callback['item_id']))


async def get_ozon_level_2(function: str):
    sellers_api = await sql.get_all_api_info()

    return await create_reply_markup(await creator_txt.create_menu_2_2(len(sellers_api)),
                                     await creator_btn.buttons_2_2(function, sellers_api))


async def get_ozon_level_3(function: str, callback):
    return await create_reply_markup(await creator_txt.create_menu_3_2(),
                                     await creator_btn.buttons_3_2(function, callback['seller']))


async def get_ozon_level_4_1(function: str, callback):
    return await create_reply_markup(await creator_txt.create_menu_4_2_1(),
                                     await creator_btn.buttons_4_2_1(function, callback['seller'], callback['option']))


async def get_order_state_menu(callback):
    """
    Menu: Ozon Express management (State selection)
    Level: 4.2.2
    Scheme: > (State) > 5.2.2
            > (State) > 5.2.2
                 ...
            > (Back) > 3.2
    """
    markup = InlineKeyboardMarkup()
    text = 'Меню управления Ozon Express\nВыберите статус заказа:'

    for item, key in ORDER_STATUS.items():
        markup.row(await create_button(key, ['ozon', '5', callback['seller'], callback['option'], item, '0', 'open']))
    markup.row(await create_button('Назад', ['ozon', '3', callback['seller'], '0', '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_ozon_level_5_1(function: str, callback):
    if callback['action'] == 'delete':
        await sql.delete_employee(int(callback['item_id']))

    users = await sql.get_users(int(callback['seller']), callback['item'])

    return await create_reply_markup(await creator_txt.create_menu_5_2_1(callback['item'], len(users)),
                                     await creator_btn.buttons_5_2_1(function, users, callback['seller'],
                                                                     callback['option'], callback['item']))


async def get_order_list_menu(callback):
    """
    Menu: Ozon Express management (User selection)
    Level: 5.2.2
    Scheme: > (Order) > 6.2
            > (Order) > 6.2
                 ...
            > (Back) > 4.2.2
    """
    markup = InlineKeyboardMarkup()
    text = f'Меню управления Ozon Express'

    orders = await get_orders_info(seller_id=int(callback['seller']), status=callback['item'])
    text += f"Количество заказов со статусом '{callback['item']}': {len(orders)}"

    for order in orders:
        markup.row(await create_button(order['posting_number'], ['ozon', '6', callback['seller'], callback['option'],
                                                                 callback['item'], order['posting_number'], 'open']))
    markup.row(await create_button('Назад', ['ozon', '4', callback['seller'], callback['option'], '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_ozon_level_6_1(function: str, callback):
    user_info = await sql.get_user_info(user_id=int(callback['item_id']))

    return await create_reply_markup(await creator_txt.create_menu_6_2_1(user_info),
                                     await creator_btn.buttons_6_2_1(function, callback['seller'], callback['option'],
                                                                     callback['item'], callback['item_id']))


async def get_order_menu(callback):
    """
    Menu: Ozon Express management (Order information)
    Level: 6.2
    Scheme: > (Reset) > 5.2.3
            > (Cancel) > 5.2.1
            > (Delete) > 5.2.3
            > (Back) > 5.2.1
    """
    markup = InlineKeyboardMarkup()

    order_info = await get_orders_info(posting_number=callback['item_id'])
    text = [f"Номер отправления: {order_info['posting_number']};",
            f"Статус: {order_info['status']};",
            f"Адрес: {order_info['address']};",
            f"Клиент: {order_info['customer_name']};",
            f"Тел. клиента: {order_info['customer_phone']};",
            f"Коментарий: {order_info['customer_comment']};",
            f"Время создания: {order_info['date_created']};",
            f"Ожидаемое время доставки: {order_info['date_shipment']};",
            f"Упаковщик: {order_info['packer_id']};",
            f"Время начала упак.: {order_info['start_package_date']};",
            f"Время завершения упак.: {order_info['finish_package_date']};",
            f"Курьер: {order_info['deliver_id']};",
            f"Время начала дост.: {order_info['start_delivery_date']};",
            f"Время завершения дост.: {order_info['finish_delivery_date']};",
            f"Успешно: {order_info['successfully']};",
            f"Причина отмены: {order_info['non_delivery_reason']};"]

    markup.row(await create_button('Сбросить', ['ozon', '5', callback['seller'], callback['option'],
                                                callback['item'], callback['item_id'], 'reset']))
    markup.row(await create_button('Отменить', ['ozon', '5', callback['seller'], callback['option'],
                                                callback['item'], callback['item_id'], 'cancel']))
    markup.row(await create_button('Удалить', ['ozon', '5', callback['seller'], callback['option'],
                                               callback['item'], callback['item_id'], 'delete']),
               await create_button('Назад', ['ozon', '5', callback['seller'], callback['option'],
                                             callback['item'], '0', 'back']))

    return {'reply_markup': markup, 'text': '\n'.join(text)}


if __name__ == '__main__':
    pass
