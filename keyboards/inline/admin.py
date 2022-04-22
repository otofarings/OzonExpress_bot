from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData
import aiogram.utils.markdown as fmt

from utils.db import sql
from utils.message import push_info_msg
from utils.formate_text import AdminMenu
from utils.ozon_express_api.request import cancel_order
from keyboards.creating import create_reply_markup, create_inline_keyboard
from utils.proccess_time import get_predict_time_for_delivery
from data.condition import FUNCTION


admin = AdminMenu()

callback_data = CallbackData('admin', 'menu', 'level', 'option', 'item', 'item_id', 'action')

menu_name = fmt.hbold("Меню Администратора")
order_menu = fmt.text("\nУправление заказами\nСписок за последние 24 часа")


async def create_button(text: str, args: list):
    return InlineKeyboardButton(text=text, callback_data=callback_data.new(*args))


# ****************************************Admin****************************************
async def get_level_1(function: str, status: str) -> dict:
    if status in ["on_shift", "reserve_package", "packaging", "delivering"]:
        buttons = [{"Заказы":       ["order", "2", "0", "0", "0", "open"]},
                   {"Сотрудники":   ["user", "2", "0", "0", "0", "open"]},
                   {"Информация":   ["info", "1", "0", "0", "0", "open"]},
                   {"Завершить смену": ["main", "1", "0", "0", "0", "finish"]}]
    else:
        buttons = [{"Начать смену":  ["main", "1", "0", "0", "0", "start"]},
                   {"Информация":    ["info", "1", "0", "0", "0", "open"]},
                   {"Выйти":         ["main", "0", "0", "0", "0", "close_bot"]}]
    text = await admin.admin_menu_1()
    return await create_reply_markup(text, function, buttons)


# ****************************************Orders****************************************
async def get_order_level_2(function: str) -> dict:
    buttons = [{"Управление 🔧":  ['order', '3', 'manage', '0', '0', 'open']},
               {"Сборка 📦":      ['package', '2', '0', '0', '0', 'open'],
                "Доставка 🛺":    ['delivery', '2', '0', '0', '0', 'open']},
               {"Назад":          ['main', '1', '0', '0', '0', 'back']}]
    text = await admin.orders_menu_2()
    return await create_reply_markup(text, function, buttons)


async def get_order_level_3(function: str, option: str, tg_id: int, tz: str) -> dict:
    orders_data = await sql.get_orders_last_day_info(tg_id, tz)

    buttons = []
    for order in orders_data:
        buttons.append({order['posting_number']: ['order', '4', option, '0', order['posting_number'], 'open']})
    buttons.append({'Назад': ['order', '2', '0', '0', '0', 'back']})
    text = await admin.orders_menu_3(len(orders_data))
    return await create_reply_markup(text, function, buttons)


async def get_order_level_4(function: str, cll: CallbackQuery) -> dict:
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
    predicted_date = await get_predict_time_for_delivery(order_info["shipment_date"], 24)

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
    text = await admin.orders_menu_4(order_info, predicted_date, callback[6])
    return await create_reply_markup(text, function, buttons)


async def get_users_for_reassign_menu(cll: CallbackQuery):
    """
    Menu: Orders management (Employee list)
    Level: 4.1.1
    Scheme:
    """
    buttons = []
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

    return


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


# ****************************************Employee****************************************
async def get_employee_level_2(function: str) -> dict:
    buttons = []
    for func in ['packer', 'courier']:
        buttons.append({FUNCTION[func].capitalize(): ['user', '3', func, '0', '0', 'open']})
    buttons.append({'Назад':               ['main', '1', '0', '0', '0', 'back']})
    text = await admin.employee_menu_2()
    return await create_reply_markup(text, function, buttons)


async def get_employee_level_3(function: str, cll: CallbackQuery) -> dict:
    callback = cll.data.split(':')

    if callback[6] == 'delete':
        await sql.delete_employee(int(callback[5]))

    users_info = await sql.get_users_info(cll.from_user.id, callback[3])

    buttons = []
    for user in users_info:
        buttons.append({user['name']: ['user', '4', callback[3], '0', user['id'], 'open']})

    buttons.append({'Назад': ['user', '2', '0', '0', '0', 'back'],
                    'Добавить': ['user', '4', callback[3], '0', '0', 'add']})
    text = await admin.employee_menu_3(callback[3])
    return await create_reply_markup(text, function, buttons)


async def get_employee_level_4(function: str, cll: CallbackQuery) -> dict:
    callback = cll.data.split(":")
    user_info = await sql.get_user_info(user_id=int(callback[5]))

    buttons = [{'Назад':   ['user', '3', callback[3], '0', '0', 'back'],
                'Удалить': ['user', '3', callback[3], '0', callback[5], 'delete']}]
    text = await admin.employee_menu_4(user_info)
    return await create_reply_markup(text, function, buttons)


async def get_user_create_back_menu(function, option):
    buttons = await create_inline_keyboard(function, [{'Назад': ['user', '3', option, '0', '0', 'cancel']}])
    return buttons
