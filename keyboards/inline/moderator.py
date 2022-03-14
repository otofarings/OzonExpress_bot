from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData

from utils.db.database import db_query
from utils.db.users import get_user_info


callback_data = CallbackData('moderator', 'menu', 'level', 'seller', 'option', 'item', 'item_id', 'action')


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
    text = 'Основное меню Модератора'

    markup.row(await create_button('Бот', ['bot', '2', '0', '0', '0', '0', 'open']))
    markup.row(await create_button('Ozon Express', ['ozon', '2', '0', '0', '0', '0', 'open']))

    return {'reply_markup': markup, 'text': text}


async def get_bot_menu():
    """
    Menu: Bot management (Option selection)
    Level: 2.1
    Scheme: > (Restart) > 2.1
            > (API) > 3.1
            > (Back) > 1
    """
    markup = InlineKeyboardMarkup()
    text = 'Меню управления ботом'

    markup.row(await create_button('Перезагрузить', ['bot', '2', '0', '0', '0', '0', 'restart']))
    markup.row(await create_button('API', ['bot', '3', '0', 'api', '0', '0', 'open']))
    markup.row(await create_button('Назад', ['main', '1', '0', '0', '0', '0', 'back']))

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

    items = await db_query(func='fetch',
                           sql="""SELECT * FROM api;""",
                           kwargs=[])

    text += f'Количество активных франчайзи: {len(items[0])}'

    for item in items[0]:
        markup.row(await create_button(item['seller_name'], ['ozon', '3', item['seller_id'],
                                                             item['seller_name'], '0', '0', 'open']))
    markup.row(await create_button('Назад', ['main', '1', '0', '0', '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_api_sellers_menu(cll: CallbackQuery):
    """
    Menu: API management (Seller selection)
    Level: 3.1
    Scheme: > (Seller) > 4.1.1
            > (Seller) > 4.1.1
                 ...
            > (Add new) > 4.1.2
            > (Back) > 2.1
    """
    callback = cll.data.split(':')

    if callback[7] == 'delete':
        await db_query(func='execute',
                       sql="""SELECT * FROM api 
                              WHERE seller_id = (SELECT seller_id
                                                 FROM employee
                                                 WHERE tg_id = $1);""",
                       kwargs=[int(callback[3])])

    markup = InlineKeyboardMarkup()
    text = f'Меню управления ботом\n'

    items = await db_query(func='fetch',
                           sql="""SELECT * FROM api;""",
                           kwargs=[])
    text += f'Количество активных франчайзи: {len(items)}'

    for item in items:
        markup.row(await create_button(item['seller_name'], ['bot', '4', item['seller_id'],
                                                             'api', item['seller_name'], '0', 'open']))
    markup.row(await create_button('Добавить', ['bot', '4', '0', 'api', '0', '0', 'add']),
               await create_button('Назад', ['bot', '2', '0', '0', '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_ozon_option_menu(callback):
    """
    Menu: Ozon Express management (Option selection)
    Level: 3.2
    Scheme: > (Admins) > 4.2.1
            > (Statistic) > 4.2.2
            > (Back) > 2.2
    """
    markup = InlineKeyboardMarkup()
    text = f'Меню управления Ozon Express\nВыберите опцию:'

    markup.row(await create_button('Админы', ['ozon', '4', callback['seller'], 'user', 'админ', '0', 'open']),
               await create_button('Статистика', ['ozon', '4', callback['seller'], 'stats', '0', '0', 'open']))
    markup.row(await create_button('Назад', ['ozon', '2', '0', '0', '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_api_seller_menu(callback):
    """
    Menu: API management (Action selection)
    Level: 4.1.1
    Scheme: > (Delete) > 3.1
            > (Back) > 3.1
    """
    markup = InlineKeyboardMarkup()
    text = f"Меню управления ботом\n{callback['item']}:\nseller_id - {callback['seller']}"

    markup.row(await create_button('Удалить', ['bot', '3', callback['seller'], 'api', callback['item'], '0', 'delete']))
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


async def get_user_list_menu(callback):
    """
    Menu: Ozon Express management (User selection)
    Level: 4.2.1
    Scheme: > (Employee) > 5.1.1
            > (Employee) > 5.1.1
                 ...
            > (Add new) > 5.1.2
            > (Back) > 3.2
    """
    markup = InlineKeyboardMarkup()
    text = "Меню управления Ozon Express\n"

    users = await db_query(func='fetch',
                           sql='get_employee',
                           kwargs=[int(callback['seller']), callback['item'], 'удален'])

    text += f"Количество {callback['item']}ов: {len(users[0])}"

    for user in users[0]:
        markup.row(await create_button(user['name'], ['ozon', '5', callback['seller'], callback['option'],
                                                      callback['item'], user['id'], 'open']))
    markup.row(await create_button('Добавить', ['ozon', '5', callback['seller'], callback['option'],
                                                callback['item'], '0', 'add']),
               await create_button('Назад', ['ozon', '3', callback['seller'], callback['option'], '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_stats_list_menu(callback):
    """
    Menu: Ozon Express management (Select stat option)
    Level: 4.2.2
    Scheme: > (Employee stat) > 5.2
            > (Orders stat) > 5.2
            > (Customers stat) > 5.2
                 ...
            > (Back) > 3.2
    """
    markup = InlineKeyboardMarkup()
    text = 'Меню управления Ozon Express\nВыберите вариант отчета:'

    markup.row(await create_button('Сотрудники', ['ozon', '5', callback['seller'],
                                                  callback['option'], 'employee', '0', 'open']))
    markup.row(await create_button('Заказы', ['ozon', '5', callback['seller'],
                                              callback['option'], 'order', '0', 'open']))
    markup.row(await create_button('Клиенты', ['ozon', '5', callback['seller'],
                                               callback['option'], 'customer', '0', 'open']))
    markup.row(await create_button('Назад', ['ozon', '3', callback['seller'], callback['option'], '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_user_menu(callback):
    """
    Menu: Ozon Express management (User information)
    Level: 5.1.1
    Scheme: > (Delete) > 4.2.3
            > (Back) > 4.2.1
    """
    markup = InlineKeyboardMarkup()

    user_info = await db_query(func='fetch',
                               sql='get_employee_info',
                               kwargs=[int(callback['item_id'])])
    added_by = await get_user_info(added_by=int(user_info[0]['added_by_id']))
    text = [f"Имя: {user_info[0]['name']};",
            f"Телефон: {user_info[0]['phone']};",
            f"Никнейм: @{user_info[0]['username']};",
            f"Должность: {user_info[0]['function']};",
            f"Статус: {user_info[0]['state']};",
            f"Дата регистрации: {str(user_info[0]['begin_date'])[:-7]};",
            f"Добавивший: @{added_by[0]['username']};"]

    markup.row(await create_button('Удалить', ['ozon', '4', callback['seller'], callback['option'],
                                               callback['item'], callback['item_id'], 'delete']),
               await create_button('Назад', ['ozon', '4', callback['seller'], callback['option'],
                                             callback['item'], '0', 'back']))

    return {'reply_markup': markup, 'text': '\n'.join(text)}


async def get_selected_stat_menu(callback):
    """
    Menu: Ozon Express management (Stat information)
    Level: 5.2
    Scheme: > (Back) > 4.2.1
    """
    markup = InlineKeyboardMarkup()

    if callback['item'] == 'employee':
        data = await db_query(func='fetch',
                              sql='employee_stat_demo',
                              kwargs=[int(callback['seller'])])
        text = ["Демо",
                f"{data[0][0]['seller_name']}",  # Название продавца
                f"Seller ID: {data[0][0]['seller_id']};\n",
                "Кол-во работников: {};",
                " -Админов: {};",
                " -Сборщиков: {};",
                " -Курьеров: {};",
                "Ожидающих активации: {};",
                "Активных: {};",
                "Удаленных: {};\n",
                "Среднее кол-во кликов в день: {};",
                "Общее кол-во кликов: {};\n",
                "Админ, добавивший больше всего сотрудников: {} - {};",
                "Сотрудник, собравший больше всего заказов: {} - {};",
                "Сотрудник, выполнивший больше всего доставок: {} - {};"]
    elif callback['item'] == 'order':
        data = []
        text = ["Демо",
                "{}",  # Название продавца
                "Seller ID: {};",
                "ID склада: {}\n"
                "Дата первого заказа: {};",
                "Дата последнего заказа: {};\n",
                "Кол-во заказов: {};",
                " -Ожидающих сборки: {};",
                " -Измененные при сборке: {};",
                " -Ожидающих доставки: {};",
                " -Успешно доставленных: {};",
                " -Недоставленных: {};",
                " -Отмененных: {};\n",
                "Самые популярные позиции:",
                " - #1: {} - {};",
                " - #2: {} - {};",
                " - #3: {} - {};\n",
                "Среднее кол-во заказов в день: {};",
                "Максимум заказов: {} - {};",
                "Минимум заказов: {} - {};",
                "Среднее время выполнения заказов: {} - {};",
                "Среднее количество товаров в заказе: {} - {};",
                "Средняя стоимость заказа: {} - {};"]
    elif callback['item'] == 'customer':
        data = []
        text = ["Демо",
                "{}",  # Название продавца
                "Seller ID: {};\n",
                "Кол-во уникальных клиентов: {};",
                " - с 1ой доставкой: {};",
                " - больше 1ой доставки: {};\n",
                "Самый частый клиент: {} - {};",
                "Больше всего отмен: {} - {};"]
    else:
        data = []
        text = ['']

    markup.row(await create_button('Назад', ['ozon', '4', callback['seller'], callback['option'], '0', '0', 'back']))

    return {'reply_markup': markup, 'text': '\n'.join(text)}


async def get_user_create_back_menu(seller_id, option, item):
    """
    Menu: Ozon Express management (User information)
    Level: 5.1.2
    Scheme: > (Back) > 4.2.1
    """
    markup = InlineKeyboardMarkup()

    markup.row(await create_button('Назад', ['ozon', '4', seller_id, option, item, '0', 'back']))

    return markup


if __name__ == '__main__':
    pass
