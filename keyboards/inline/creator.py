from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from data.condition import ORDER_STATE
from utils.db_api.users import get_users, get_user_info
from utils.db_api.orders import get_orders_info
from utils.db_api import extra


callback_data = CallbackData('creator', 'menu', 'level', 'seller', 'option', 'item', 'item_id', 'action')

FUNCTIONS = {
    'модератор': 'Модераторы',
    'админ': 'Админы',
    'сборщик': 'Сборщики',
    'курьер': 'Курьеры'
}


async def create_button(text: str, args: list):
    return InlineKeyboardButton(text=text, callback_data=callback_data.new(*args))


async def get_main_menu():
    """
    Menu: Main
    Level: 1
    Scheme: > (Bot) > 2.1
            > (Ozon Express) > 2.2
    """
    markup = InlineKeyboardMarkup()
    markup.row(await create_button('Бот', ['bot', '2', '0', '0', '0', '0', 'open']))
    markup.row(await create_button('Ozon Express', ['ozon', '2', '0', '0', '0', '0', 'open']))
    text = 'Основное меню'
    return {'reply_markup': markup, 'text': text}


async def get_bot_menu():
    """
    Menu: Bot management (Option selection)
    Level: 2.1
    Scheme: > (Restart) > 2.1
            > (Turn off) > 2.1
            > (API) > 3.1
            > (Back) > 1
    """
    markup = InlineKeyboardMarkup()
    markup.row(await create_button('Перезагрузить', ['bot', '2', '0', '0', '0', '0', 'restart']))
    markup.row(await create_button('Выключить', ['bot', '2', '0', '0', '0', '0', 'turn_off']))
    markup.row(await create_button('API', ['bot', '3', '0', 'api', '0', '0', 'open']))
    markup.row(await create_button('Назад', ['main', '1', '0', '0', '0', '0', 'back']))
    text = 'Меню управления ботом'
    return {'reply_markup': markup, 'text': text}


async def get_ozon_sellers_menu():
    """
    Menu: Ozon Express management (Seller selection)
    Level: 2.2
    Scheme: > (Seller) > 3.2
            > (Seller) > 3.2
                 ...
            > (Back) > 1
    """
    markup = InlineKeyboardMarkup()
    text = 'Меню управления Ozon Express\n'

    items = await extra.get_all_api()
    text += f'Количество активных франчайзи: {len(items)}'

    for item in items:
        markup.row(await create_button(item['seller_name'], ['ozon', '3', item['seller_id'],
                                                             item['seller_name'], '0', '0', 'open']))
    markup.row(await create_button('Назад', ['main', '1', '0', '0', '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_api_sellers_menu():
    """
    Menu: API management (Seller selection)
    Level: 3.1
    Scheme: > (Seller) > 4.1.1
            > (Seller) > 4.1.1
                 ...
            > (Add new) > 4.1.2
            > (Back) > 2.1
    """
    markup = InlineKeyboardMarkup()
    text = 'Меню управления ботом\n'

    items = await extra.get_all_api()
    text += f'Количество активных франчайзи: {len(items)}'

    for item in items:
        markup.row(await create_button(item['seller_name'], ['bot', '4', item['seller_id'], 'api',
                                                             item['seller_name'], '0', 'open']))
    markup.row(await create_button('Добавить', ['bot', '4', '0', 'api', '0', '0', 'add']),
               await create_button('Назад', ['bot', '2', '0', '0', '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_ozon_option_menu(callback):
    """
    Menu: Ozon Express management (Option selection)
    Level: 3.2
    Scheme: > (Employee) > 4.2.1
            > (Orders) > 4.2.2
            > (Back) > 2.2
    """
    markup = InlineKeyboardMarkup()
    text = 'Меню управления Ozon Express\nВыберите опцию:'

    markup.row(await create_button('Сотрудники', ['ozon', '4', callback['seller'], 'user', '0', '0', 'open']),
               await create_button('Заказы', ['ozon', '4', callback['seller'], 'order', '0', '0', 'open']))
    markup.row(await create_button('Назад', ['ozon', '2', '0', '0', '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_api_seller_menu(callback):
    """
    Menu: API management (Action selection)
    Level: 4.1.1
    Scheme: > (Replace API key) > 5.1
            > (Delete) > 3.1
            > (Back) > 3.1
    """
    markup = InlineKeyboardMarkup()
    text = f"Меню управления ботом\n{callback['item']}:\nseller_id - {callback['seller']}"

    markup.row(await create_button('Заменить API ключ', ['bot', '5', callback['seller'], 'api',
                                                         callback['item'], '0', 'replace']),
               await create_button('Удалить', ['bot', '3', callback['seller'], 'api',
                                               callback['item'], '0', 'delete']))
    markup.row(await create_button('Назад', ['bot', '3', '0', 'api', '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_api_create_back_menu():
    """
    Menu: API management (Back from adding new)
    Level: 4.1.2
    Scheme: > (Back) > 3.1
    """
    markup = InlineKeyboardMarkup()

    markup.row(await create_button('Назад', ['bot', '3', '0', 'api', '0', '0', 'back']))

    return markup


async def get_user_function_menu(callback):
    """
    Menu: Ozon Express management (Function selection)
    Level: 4.2.1
    Scheme: > (Function) > 5.2.1
            > (Function) > 5.2.1
                 ...
            > (Back) > 3.2
    """
    markup = InlineKeyboardMarkup()
    text = 'Меню управления Ozon Express\nВыберите должность:'

    for item, key in FUNCTIONS.items():
        markup.row(await create_button(key, ['ozon', '5', callback['seller'], callback['option'], item, '0', 'open']))
    markup.row(await create_button('Назад', ['ozon', '3', callback['seller'], '0', '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


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

    for item, key in ORDER_STATE.items():
        markup.row(await create_button(key, ['ozon', '5', callback['seller'], callback['option'], item, '0', 'open']))
    markup.row(await create_button('Назад', ['ozon', '3', callback['seller'], '0', '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_api_replace_back_menu(callback):
    """
    Menu: API management (Back from replacing key)
    Level: 5.1
    Scheme: > (Back) > 4.1.1
    """
    markup = InlineKeyboardMarkup()

    markup.row(await create_button('Назад', ['bot', '4', callback['seller'], 'api', '0', callback['item'], 'back']))

    return markup


async def get_user_list_menu(callback):
    """
    Menu: Ozon Express management (User selection)
    Level: 5.2.1
    Scheme: > (Employee) > 6.1.1
            > (Employee) > 6.1.1
                 ...
            > (Add new) > 6.1.2
            > (Back) > 4.2.1
    """
    markup = InlineKeyboardMarkup()
    text = f"Меню управления Ozon Express\nКоличество {callback['item']}ов: "

    users = await get_users(seller_id=int(callback['seller']), function=callback['item'])
    text += f"{len(users)}"

    for user in users:
        markup.row(await create_button(user['name'], ['ozon', '6', callback['seller'], callback['option'],
                                                      callback['item'], user['id'], 'open']))
    markup.row(await create_button('Добавить', ['ozon', '6', callback['seller'], callback['option'],
                                                callback['item'], '0', 'add']),
               await create_button('Назад', ['ozon', '4', callback['seller'], callback['option'], '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


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


async def get_user_menu(callback):
    """
    Menu: Ozon Express management (User information)
    Level: 6.1.1
    Scheme: > (Delete) > 5.2.3
            > (Back) > 5.2.1
    """
    markup = InlineKeyboardMarkup()

    user_info = await get_user_info(user_id=int(callback['item_id']))
    added_by = await get_user_info(added_by=int(user_info[0]['added_by_id']))
    text = [f"Имя: {user_info[0]['name']};",
            f"Телефон: {user_info[0]['phone']};",
            f"Никнейм: @{user_info[0]['username']};",
            f"Должность: {user_info[0]['function']};",
            f"Статус: {user_info[0]['state']};",
            f"Дата регистрации: {str(user_info[0]['begin_date'])[:-7]};",
            f"Добавивший: @{str(added_by[0]['username'])};"]

    markup.row(await create_button('Удалить', ['ozon', '5', callback['seller'],
                                               callback['option'], callback['item'], callback['item_id'], 'delete']),
               await create_button('Назад', ['ozon', '5', callback['seller'],
                                             callback['option'], callback['item'], '0', 'back']))

    return {'reply_markup': markup, 'text': '\n'.join(text)}


async def get_user_create_back_menu(seller_id, option, item):
    """
    Menu: Ozon Express management (User information)
    Level: 6.1.2
    Scheme: > (Back) > 5.2.1
    """
    markup = InlineKeyboardMarkup()

    markup.row(await create_button('Назад', ['ozon', '5', seller_id, option, item, '0', 'back']))

    return markup


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
