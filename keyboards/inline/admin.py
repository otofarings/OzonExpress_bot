from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData
import aiogram.utils.markdown as fmt

from utils.db import sql
from utils.geo import get_map_url
from utils.message import push_info_msg
from utils.ozon_express_api.request import cancel_order
from keyboards.creating import create_inline_keyboard
from data.condition import CANCELLATION_STATUS, FUNCTION, USERS_STATE

callback_data = CallbackData('admin', 'menu', 'level', 'option', 'item', 'item_id', 'action')

menu_name = fmt.hbold("Меню Администратора")
order_menu = fmt.text("\nУправление заказами\nСписок за последние 24 часа")


async def create_button(text: str, args: list):
    return InlineKeyboardButton(text=text, callback_data=callback_data.new(*args))


# ****************************************Admin****************************************
async def get_level_1(function: str, status: str) -> dict:
    text = [fmt.hbold("Меню Администратора 👔")]

    if status in ["on_shift", "reserve_package", "packaging", "delivering"]:
        buttons = [{"Заказы":       ["order", "2", "0", "0", "0", "open"]},
                   {"Сотрудники":   ["user", "2", "0", "0", "0", "open"]},
                   {"Информация":   ["info", "1", "0", "0", "0", "open"]},
                   {"Завершить смену": ["main", "1", "0", "0", "0", "finish"]}]
    else:
        buttons = [{"Начать смену":  ["main", "1", "0", "0", "0", "start"]},
                   {"Информация":    ["info", "1", "0", "0", "0", "open"]},
                   {"Выйти":         ["main", "0", "0", "0", "0", "close_bot"]}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


# ****************************************Orders****************************************
async def get_order_level_2(function: str) -> dict:
    text = [fmt.hbold("Меню Администратора 👔"), fmt.hbold("\nЗаказы")]

    buttons = [{"Управление 🔧":  ['order', '3', 'manage', '0', '0', 'open']},
               {"Сборка 📦":      ['package', '2', '0', '0', '0', 'open'],
                "Доставка 🛺":    ['delivery', '2', '0', '0', '0', 'open']},
               {"Назад":          ['main', '1', '0', '0', '0', 'back']}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_order_level_3(function: str, option: str, tg_id: int, tz: str) -> dict:
    text = [fmt.hbold("Меню управления заказами 🔧")]

    orders_data = await sql.get_orders_last_day_info(tg_id, tz)

    text.append(fmt.text("\nДоступно:", fmt.hbold(len(orders_data))))

    buttons = []
    for order in orders_data:
        buttons.append({order['posting_number']: ['order', '4', option, '0', order['posting_number'], 'open']})

    buttons.append({'Назад': ['order', '2', '0', '0', '0', 'back']})

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_order_level_4(function: str, cll: CallbackQuery) -> dict:
    text = [fmt.hbold("Меню управления заказами 🔧")]

    callback = cll.data.split(':')

    if callback[6] == 'assign':
        await push_info_msg(cll, 'Опция временно не доступна!')
        # await orders.reassign(callback['item'], callback['item_id'])
        # user = await get_user_info(callback['item'])
        # if user[0]['function'] == FUNCTION['collector']:
        #     await get_package_order_menu({'order', '5', '0', '0', callback['item_id'], 'open'})
        #     await dp.bot.edit_message_text(chat_id=user[0]['tg_id'], message_id=user[0]['msg_id'],
        #                                    **await get_package_order_menu(
        #                                        {'option': '0', 'item_id': callback['item_id'], 'action': 'open'}))
        # else:
        #     await get_package_order_menu({'order', '5', '0', '0', callback['item_id'], 'open'})
        #     await dp.bot.edit_message_text(chat_id=user[0]['tg_id'], message_id=user[0]['msg_id'],
        #                                    **await get_package_order_menu(
        #                                        {'option': '0', 'item_id': callback['item_id'], 'action': 'open'}))
    elif callback[6] == 'cancel':
        await push_info_msg(cll, 'Заказ был отменен')
        await cancel_order(callback[5], cll.from_user.id, int(callback[3]))

    order_info = await sql.get_order_info(callback[5])

    status = await translate_order_status(order_info['status'] if callback[6] != 'cancel' else 'cancelled')
    text = [fmt.text(fmt.hbold("Отправление:"), order_info['posting_number']),
            fmt.text(fmt.hbold("\nСтатус:"), status),
            fmt.text(fmt.hbold("Создан:"), order_info['in_process_at']),
            fmt.text("_" * 30),
            fmt.text(fmt.hbold("Покупатель:"), fmt.hitalic(order_info['customer_name'])),
            fmt.text(fmt.hbold("Тел. покупателя:"), fmt.hcode(order_info['customer_phone'])),
            fmt.text("_" * 30),
            fmt.text(fmt.hbold("Получатель:"), fmt.hitalic(order_info['addressee_name'])),
            fmt.text(fmt.hbold("Тел. получателя:"), fmt.hcode(order_info['addressee_phone'])),
            fmt.text("_" * 30),
            fmt.text(fmt.hbold("Коментарий:"), order_info['customer_comment']),
            fmt.text("_" * 30),
            fmt.text(fmt.hbold("Адрес:"), fmt.hlink(order_info["address"], await get_map_url(order_info["latitude"],
                                                                                             order_info["longitude"]))),
            fmt.text("_" * 30),
            fmt.text(fmt.hbold("Сборщик:"), fmt.hlink("сотрудник", f"tg://user?id={order_info['packer_id']}")),
            fmt.text(fmt.hbold("Начало упак.:"), await check_empty_status(order_info['start_package_date'])),
            fmt.text(fmt.hbold("Завершение упак.:"), await check_empty_status(order_info['finish_package_date'])),
            fmt.text("_" * 30),
            fmt.text(fmt.hbold("Передать курьеру до:"), await check_empty_status(order_info['shipment_date'])),
            fmt.text(fmt.hbold("Курьер:"),
                     await check_empty_status(fmt.hlink("сотрудник", f"tg://user?id={order_info['deliver_id']}"))),
            fmt.text(fmt.hbold("Начало дост.:"), await check_empty_status(order_info['start_delivery_date'])),
            fmt.text(fmt.hbold("Завершение дост.:"), await check_empty_status(order_info['finish_delivery_date'])),
            fmt.text("_" * 30),
            fmt.text(fmt.hbold("Отмена:"), await check_empty_status(order_info['cancel_reason_id'])),
            fmt.text(fmt.hbold("Причина отмены:"), await check_empty_status(order_info['cancel_reason'])),
            fmt.text(fmt.hbold("Отменивший:"), await check_empty_status(order_info['cancellation_initiator']))]

    buttons = []
    if order_info:
        if order_info['start_delivery_date']:
            option = FUNCTION['courier']
        elif order_info['start_package_date']:
            option = FUNCTION['packer']
        else:
            option = '0'

        if option and option != '0':
            buttons.append({'Переназначить': ['order', '4', option, '0', callback[5], 'reassign']})

    if not order_info['cancel_reason_id']:
        buttons.append({'Отменить': ['order', '5', '0', '0', callback[5], 'start_cancel']})

    buttons.append({'Назад': ['order', '3', callback[3], '0', '0', 'back']})

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_users_for_reassign_menu(cll: CallbackQuery):
    """
    Menu: Orders management (Employee list)
    Level: 4.1.1
    Scheme:
    """
    markup = InlineKeyboardMarkup()
    text = f"Меню управления заказами\n"

    # callback = cll.data.split(':')
    # users_info = await start_connection(func='fetch',
    #                                     sql='get_employee_special_v2',
    #                                     kwargs=[tg_id = cll.from_user.id, function = callback[-4], 'удален'])
    # text += f"Переназначение заказа {callback[-2]}\nКоличество свободных сотрудников: {len(users_info)}"
    #
    # for user in users_info:
    #     markup.row(await create_button(user['name'], ['order', '5', callback[-4], user['id'], callback[-2], 'open']))
    # markup.row(await create_button('Назад', ['order', '3', '0', '0', callback[-2], 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_user_for_reassign_menu(cll: CallbackQuery = None, state=None):
    """
    Menu: Orders management (Employee info)
    Level: 5.1
    Scheme: > (Assign) > 3.1
            > (Back) > 4.1.1
    """
    # if cll:
    #     await save_previous(cll.message.text, cll.message.reply_markup, state, first=True)
    #
    #     markup = InlineKeyboardMarkup()
    #
    #     callback = cll.data.split(':')
    #     user_info = await db_query(func='fetch',
    #                                sql='get_employee_by_tg_id',
    #                                kwargs=[callback[-3]])
    #     # Заменить
    #     user_info = await get_user_info(user_id=int(callback[-3]))
    #     added_by = await get_user_info(user_tg_id=int(user_info[0]['added_by_id']))
    #     text = [f"Переназначение отправления:\n{callback[-2]}\n",
    #             f"Имя: \n{user_info[0]['name']};",
    #             f"Телефон: \n{user_info[0]['phone']};",
    #             f"Никнейм: @{user_info[0]['username']};",
    #             f"Должность: {user_info[0]['function']};",
    #             f"Статус: {user_info[0]['state']};",
    #             f"Дата регистрации: \n{str(user_info[0]['begin_date'])[:-7]};",
    #             f"Добавивший: @{str(added_by[0]['username'])};"]
    #
    #     markup.row(await create_button('Назад', ['order', '5', callback[-4], '0',
    #                                              callback[-2], 'back']),
    #                await create_button('Назначить', ['order', '3', callback[-4], callback[-3],
    #                                                  callback[-2], 'assign']))
    #
    #     return {'reply_markup': markup, 'text':  '\n'.join(text)}
    #
    # else:
    #     return await save_previous(state=state, get=True, last=True, menu=True)


async def get_reasons_for_cancel_menu(callback):
    """
    Menu: Orders management (Employee list)
    Level: 4.1.2
    Scheme: > (Reason) > 3.1
            > (Reason) > 3.1
                 ...
            > (Another reason) > 3.1
            > (Back) > 3.1
    """
    markup = InlineKeyboardMarkup()
    text = [f"Меню управления заказами\nОтмена заказа {callback['item_id']}\n",
            "Выберете причину или введите свою, нажав 'Другая причина'"]

    for key, item in CANCELLATION_STATUS.items():
        markup.row(await create_button(item.capitalize(), ['order', '4', key, '0', callback['item_id'], 'cancel']))
    markup.row(await create_button('Назад', ['order', '3', callback['option'], '0', callback['item_id'], 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_order_cancel_back_menu(callback):
    markup = InlineKeyboardMarkup()

    markup.row(await create_button('Назад', ['order', '4', callback['option'], '0', callback['item_id'], 'cancel']))

    return {'reply_markup': markup}


# ****************************************Employee****************************************
async def get_employee_level_2(function: str) -> dict:
    text = [fmt.hbold("Меню Администратора 👔"),
            fmt.hbold("\nСотрудники 👥"),
            fmt.text("\nВыберите должность:")]

    buttons = []
    for func in ['packer', 'courier']:
        buttons.append({FUNCTION[func].capitalize(): ['user', '3', func, '0', '0', 'open']})
    buttons.append({'Назад':               ['main', '1', '0', '0', '0', 'back']})

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_employee_level_3(function: str, cll: CallbackQuery) -> dict:
    text = [fmt.hbold("Меню Администратора 👔"),
            fmt.hbold("\nСотрудники 👥")]

    callback = cll.data.split(':')

    if callback[6] == 'delete':
        await sql.delete_employee(int(callback[5]))

    users_info = await sql.get_users_info(cll.from_user.id, callback[3])
    text.append(fmt.text(f'\nКоличество {FUNCTION[callback[3]]}ов: {len(users_info)}'))

    buttons = []
    for user in users_info:
        buttons.append({user['name']: ['user', '4', callback[3], '0', user['id'], 'open']})

    buttons.append({'Назад': ['user', '2', '0', '0', '0', 'back'],
                    'Добавить': ['user', '4', callback[3], '0', '0', 'add']})

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_employee_level_4(function: str, cll: CallbackQuery) -> dict:
    callback = cll.data.split(":")
    user_info = await sql.get_user_info(user_id=int(callback[5]))
    text = [f"Имя: {user_info['name']};",
            f"Телефон: {user_info['phone']};",
            f"Никнейм: @{user_info['username']};",
            f"Должность: {FUNCTION[user_info['function']]};",
            f"Статус: {USERS_STATE[user_info['state']]};",
            f"Дата регистрации: {str(user_info['begin_date'])[:-7]};",
            f"Добавивший: @{str(user_info['added_by_name'])};"]

    buttons = [{'Назад':   ['user', '3', callback[3], '0', '0', 'back'],
                'Удалить': ['user', '3', callback[3], '0', callback[5], 'delete']}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_user_create_back_menu(option):
    """
    Menu: Ozon Express management (User information)
    Level: 4.2.2
    Scheme: > (Back) > 3.2
    """
    markup = InlineKeyboardMarkup()

    markup.row(await create_button('Назад', ['user', '3', option, '0', '0', 'cancel']))

    return markup


async def translate_order_status(status: str) -> str:
    order_status = {
        "delivered": "Доставлен",
        "awaiting_packaging": "Ожидает сборки",
        "awaiting_deliver": "Ожидает отгрузки",
        "cancelled": "Отменён",
        "packaging": "Собирается",
        "delivering": "Доставляется",
        "undelivered": "Не доставлен",
        "conditionally_delivered": "Условно доставлен"
    }
    return order_status[status]


async def check_empty_status(status: str) -> str:
    return status if status else "Отсутствует"
