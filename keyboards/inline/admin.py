from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher import Dispatcher
import aiogram.utils.markdown as fmt

from states.fsm import finish_state
from utils.db_api import extra, orders
from utils.db_api.database import db_query
from utils.db_api.message import push_info_msg
from utils.db_api.extra import get_map_url, save_previous
from utils.db_api.users import get_user_info
from utils.ozon_express_api.request import cancel_order, start_delivery_last_mile, complete_delivery_ozon
from data.config import MODER_LOGS, DEBUG
from data.condition import CANCELLATION_STATUS, FUNCTION
from utils.proccess_time import get_time
from utils.ozon_express_api.request import get_info, complete_packaging_ozon, start_delivery

callback_data = CallbackData('admin', 'menu', 'level', 'option', 'item', 'item_id', 'action')

menu_name = fmt.hbold("Меню Администратора")
order_menu = fmt.text("\nУправление заказами\nСписок за последние 24 часа")


async def create_button(text: str, args: list):
    return InlineKeyboardButton(text=text, callback_data=callback_data.new(*args))


async def send_info_log(dp: Dispatcher, cll: CallbackQuery, action: str, ex_option=None):

    api = await db_query(func='fetch',
                         sql="""SELECT * FROM api 
                                        WHERE seller_id = (SELECT seller_id FROM employee WHERE tg_id = $1 );""",
                         kwargs=[cll.from_user.id])
    user_info = await db_query(func='fetch',
                               sql="""SELECT * FROM employee WHERE tg_id = $1;""",
                               kwargs=[cll.from_user.id])

    await dp.bot.send_message(chat_id=MODER_LOGS if DEBUG else api[0][0]["log_chat_id"],
                              text=fmt.text(ex_option if ex_option else "",
                                            fmt.hitalic(str(await get_time(tz=api[0][0]["timezone"]))[:-7]),
                                            fmt.text(fmt.hbold("Админ: "),
                                                     fmt.hlink(f"{user_info[0][0]['name']}",
                                                               f"tg://user?id={cll.from_user.id}")),
                                            fmt.text(fmt.hbold("Действие: "), action),
                                            sep="\n"))
    return


async def check_action_start_menu(callback, cll, dp, tz=None):
    if callback[-1] == "back":
        print(callback)
        if callback[1] == 'delivery':
            print('ok')
            await db_query(func='fetch',
                           sql="""WITH updated AS (UPDATE order_info SET status = $3, deliver_id = $4
                                                   WHERE status = $2 AND deliver_id = $1 RETURNING *)
                                  SELECT count(posting_number) FROM updated 
                                  WHERE status = $3 AND warehouse_id IN (SELECT warehouse_id FROM employee
                                                                         WHERE tg_id = $1);""",
                           kwargs=[cll.from_user.id, 'reserved_by_deliver', 'awaiting_deliver', None])

        else:
            await db_query(func='execute',
                           sql="""UPDATE order_info SET status = $2, packer_id = $4 
                                                  WHERE packer_id = $1 AND status = $3;""",
                           kwargs=[cll.from_user.id, 'awaiting_packaging', 'reserved_by_packer', None])

    elif callback[-1] == "finish":
        await send_info_log(dp, cll, "Вернулся на склад")

    elif callback[-1] == "cancel":
        if callback[-4] == "402":
            pass

        else:
            await db_query(func="execute",
                           sql="cancel_packaging",
                           kwargs=[callback[-2], "canceled", (await get_time(tz=tz)).replace(tzinfo=None),
                                   "canceled", int(callback[-4]), CANCELLATION_STATUS[int(callback[-4])],
                                   "seller", "Продавец"])

            await send_info_log(dp, cll, "Отменил заказ", fmt.text(fmt.hbold("Заказ: "), fmt.hcode(callback[-2])))
            await push_info_msg(cll, "Заказ отменен!")
    return


# ****************************************Main****************************************
async def get_main_menu():
    """
    Menu: Main
    Level: 1
    Scheme: > (Orders) > 2.1
            > (Employee) > 2.2
    """
    markup = InlineKeyboardMarkup()

    markup.row(await create_button('Заказы', ['order', '2', '0', '0', '0', 'open']))
    markup.row(await create_button('Сотрудники', ['user', '2', '0', '0', '0', 'open']))

    return {'reply_markup': markup, 'text': fmt.text(menu_name)}


# ****************************************Orders****************************************
async def get_preorders_menu(cll: CallbackQuery):
    """
    Menu: Orders
    Level: 2
    """
    markup = InlineKeyboardMarkup()
    callback = cll.data.split(':')
    if (callback[-1] == 'reserve_back') and (callback[3] == 'packer'):
        await db_query(func='fetch',
                       sql=f"""UPDATE order_info SET status = $3, {callback[3]}_id = $4 
                                       WHERE status = $2 AND {callback[3]}_id = $1;""",
                       kwargs=[cll.message.chat.id, 'reserved_by_packer', 'awaiting_packaging', None])

    markup.row(await create_button('Управление заказами', ['order', '3', 'manage', '0', '0', 'open']))
    markup.row(await create_button('Сборка', ['package', '2', '0', '0', '0', 'open']),
               await create_button('Доставка', ['delivery', '2', '0', '0', '0', 'open']))
    markup.row(await create_button('Назад', ['main', '1', '0', '0', '0', 'back']))

    return {'reply_markup': markup, 'text': fmt.text(menu_name)}


async def get_orders_menu(cll: CallbackQuery, tz: str):
    """
    Menu: Orders management (Orders list)
    Level: 3
    """
    markup = InlineKeyboardMarkup()
    callback = cll.data.split(':')

    orders_data = await db_query(func='fetch',
                                 sql="""SELECT * FROM order_info WHERE in_process_at > $2 
                                                    AND warehouse_id IN (SELECT warehouse_id FROM employee 
                                                                         WHERE tg_id = $1);""",
                                 kwargs=[cll.message.chat.id,
                                                 (await get_time(24, minus=True, tz=tz)).replace(tzinfo=None)])

    info_text = fmt.text("\nКоличество: ", fmt.hbold(len(orders_data[0])))

    for order in orders_data[0]:
        markup.row(await create_button(f"{order['posting_number']}",
                                       ['order', '4', callback[3], '0', order['posting_number'], 'open']))
    markup.row(await create_button('Назад', ['order', '2', '0', '0', '0', 'reserve_back']))

    return {'reply_markup': markup, 'text': fmt.text(menu_name, order_menu, info_text)}


async def get_orders_list_menu(dp: Dispatcher, cll: CallbackQuery):
    """
    Menu: Orders management (Order info)
    Level: 3.1
    Scheme: > (Reassign) > 4.1.1
            > (Cancel) > 4.1.2
            > (Back) > 2.1
    """
    markup = InlineKeyboardMarkup()
    callback = cll.data.split(':')

    if callback[-1] == 'assign':
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
    elif callback[-1] == 'cancel':
        await push_info_msg(cll, 'Заказ был отменен')
        await cancel_order(callback[-2], cll.from_user.id, int(callback[3]))

    order_info = await db_query(func='fetch',
                                sql="""SELECT * FROM order_info WHERE posting_number = $1;""",
                                kwargs=[callback[-2]])

    info_text = fmt.text(fmt.text(fmt.hbold("\nНомер отправления: "), order_info[0][0]['posting_number']),
                         fmt.text(fmt.hbold("Статус: "), order_info[0][0]['status'] if callback[-1] != 'cancel' else 'canceled'),
                         fmt.text(fmt.hbold("\nСоздан: "), order_info[0][0]['in_process_at']),
                         fmt.text(fmt.hbold("Доставить до: "), order_info[0][0]['shipment_date']),
                         fmt.text(fmt.hbold("\nПокупатель: "), fmt.hitalic(order_info[0][0]['customer_name'])),
                         fmt.text(fmt.hbold("Тел. покупателя: "), fmt.hcode(order_info[0][0]['customer_phone'])),
                         fmt.text(fmt.hbold("Получатель: "), fmt.hitalic(order_info[0][0]['addressee_name'])),
                         fmt.text(fmt.hbold("Тел. получателя: "), fmt.hcode(order_info[0][0]['addressee_phone'])),
                         fmt.text(fmt.hbold("Коментарий: "), order_info[0][0]['customer_comment']),
                         fmt.text(fmt.hbold("\nАдрес: "), fmt.hlink(order_info[0][0]["address"],
                                                                    await get_map_url(
                                                                        order_info[0][0]["latitude"],
                                                                        order_info[0][0]["longitude"]))),
                         fmt.text(fmt.hbold("\nСборщик: "), fmt.hlink("сотрудник",
                                                                      f"tg://user?id={order_info[0][0]['packer_id']}")),
                         fmt.text(fmt.hbold("Начало упак.: "), order_info[0][0]['start_package_date']),
                         fmt.text(fmt.hbold("Завершение упак.: "), order_info[0][0]['finish_package_date']),
                         fmt.text(fmt.hbold("Курьер: "), fmt.hlink("сотрудник",
                                                                   f"tg://user?id={order_info[0][0]['deliver_id']}")),
                         fmt.text(fmt.hbold("Начало дост.: "), order_info[0][0]['start_delivery_date']),
                         fmt.text(fmt.hbold("Завершение дост.: "), order_info[0][0]['finish_delivery_date']),
                         fmt.text(fmt.hbold("\nОтмена: "), order_info[0][0]['cancel_reason_id']),
                         fmt.text(fmt.hbold("Причина отмены: "), order_info[0][0]['cancel_reason']),
                         fmt.text(fmt.hbold("Отменивший: "), order_info[0][0]['cancellation_initiator']),
                         sep="\n")

    if order_info[0][0]:
        if order_info[0][0]['start_delivery_date']:
            option = FUNCTION['courier']
        elif order_info[0][0]['start_package_date']:
            option = FUNCTION['collector']
        else:
            option = '0'

        if option and option != '0':
            markup.row(await create_button('Переназначить', ['order', '4', option, '0', callback[-2], 'reassign']))

    if not order_info[0][0]['cancel_reason_id']:
        markup.row(await create_button('Отменить', ['order', '5', '0', '0', callback[-2], 'cancel']))

    markup.row(await create_button('Назад', ['order', '3', callback[3], '0', '0', 'reserve_back']))

    return {'reply_markup': markup, 'text': fmt.text(menu_name, order_menu, info_text, sep="\n")}


async def get_users_for_reassign_menu(cll: CallbackQuery):
    """
    Menu: Orders management (Employee list)
    Level: 4.1.1
    Scheme:
    """
    markup = InlineKeyboardMarkup()
    text = f"Меню управления заказами\n"

    callback = cll.data.split(':')
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
    if cll:
        await save_previous(cll.message.text, cll.message.reply_markup, state, first=True)

        markup = InlineKeyboardMarkup()

        callback = cll.data.split(':')
        user_info = await db_query(func='fetch',
                                   sql='get_employee_by_tg_id',
                                   kwargs=[callback[-3]])
        # Заменить
        user_info = await get_user_info(user_id=int(callback[-3]))
        added_by = await get_user_info(user_tg_id=int(user_info[0]['added_by_id']))
        text = [f"Переназначение отправления:\n{callback[-2]}\n",
                f"Имя: \n{user_info[0]['name']};",
                f"Телефон: \n{user_info[0]['phone']};",
                f"Никнейм: @{user_info[0]['username']};",
                f"Должность: {user_info[0]['function']};",
                f"Статус: {user_info[0]['state']};",
                f"Дата регистрации: \n{str(user_info[0]['begin_date'])[:-7]};",
                f"Добавивший: @{str(added_by[0]['username'])};"]

        markup.row(await create_button('Назад', ['order', '5', callback[-4], '0',
                                                 callback[-2], 'back']),
                   await create_button('Назначить', ['order', '3', callback[-4], callback[-3],
                                                     callback[-2], 'assign']))

        return {'reply_markup': markup, 'text':  '\n'.join(text)}

    else:
        return await save_previous(state=state, get=True, last=True, menu=True)


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
    """
    Menu: API management (Back from reassigning employee on order)
    Level: 3.1
    Scheme: > (Back) > 3.1
    """
    markup = InlineKeyboardMarkup()

    markup.row(await create_button('Назад', ['order', '4', callback['option'], '0', callback['item_id'], 'cancel']))

    return {'reply_markup': markup}


# ****************************************Employee****************************************
async def get_employee_menu():
    """
    Menu: Employee management (Option selection)
    Level: 2.1
    Scheme: > (Collectors) > 3.2
            > (Couriers) > 3.2
            > (Back) > 1
    """
    markup = InlineKeyboardMarkup()
    text = 'Меню управления персоналом\nВыберите должность:'

    for item, key in {'collector': 'сборщик', 'courier': 'курьер'}.items():
        markup.row(await create_button(key.capitalize(), ['user', '3', key, '0', '0', 'open']))
    markup.row(await create_button('Назад', ['main', '1', '0', '0', '0', 'back']))

    return {'reply_markup': markup, 'text': text}


async def get_users_menu(cll: CallbackQuery):
    """
    Menu: Employee management (Employee list)
    Level: 3.2
    Scheme: > (Employee) > 4.2.1
            > (Employee) > 4.2.1
                 ...
            > (Add new) > 4.2.2
            > (Back) > 2.2
    """
    markup = InlineKeyboardMarkup()

    callback = cll.data.split(':')
    if callback[-1] == 'delete':
        await db_query(func='execute',
                       sql="""UPDATE employee SET state = $1, end_date = $2 WHERE id = $3;""",
                       kwargs=['удален', await get_time(), int(callback[-2])])

    users_info = await db_query(func='fetch',
                                sql="""SELECT name, id FROM employee WHERE function = $2 AND state != $3
                                               AND warehouse_id IN (SELECT warehouse_id 
                                                                    FROM employee WHERE tg_id = $1);""",
                                kwargs=[cll.from_user.id, callback[-4], 'удален'])
    text = f'Меню управления персоналом\nКоличество {callback[-4]}ов: {len(users_info[0])}'

    for user in users_info[0]:
        markup.row(await create_button(user['name'], ['user', '4', callback[-4], '0', user['id'], 'open']))
    markup.row(await create_button('Назад', ['user', '2', '0', '0', '0', 'back']),
               await create_button('Добавить', ['user', '4', callback[-4], '0', '0', 'add']))

    return {'reply_markup': markup, 'text': text}


async def get_user_menu(callback):
    """
    Menu: Employee management (Employee info)
    Level: 4.2.1
    Scheme: > (Delete) > 3.2
            > (Back) > 3.2
    """
    markup = InlineKeyboardMarkup()

    user_info = await db_query(func='fetch',
                               sql="""SELECT * FROM employee WHERE id = $1;""",
                               kwargs=[int(callback['item_id'])])
    added_by = await db_query(func='fetch',
                              sql="""SELECT * FROM employee WHERE tg_id = $1;""",
                              kwargs=[int(user_info[0][0]['added_by_id'])])
    text = [f"Имя: {user_info[0][0]['name']};",
            f"Телефон: {user_info[0][0]['phone']};",
            f"Никнейм: @{user_info[0][0]['username']};",
            f"Должность: {user_info[0][0]['function']};",
            f"Статус: {user_info[0][0]['state']};",
            f"Дата регистрации: {str(user_info[0][0]['begin_date'])[:-7]};",
            f"Добавивший: @{str(added_by[0][0]['username'])};"]

    markup.row(await create_button('Назад', ['user', '3', callback['option'], '0', '0', 'back']),
               await create_button('Удалить', ['user', '3', callback['option'], '0', callback['item_id'], 'delete']))

    return {'reply_markup': markup, 'text': '\n'.join(text)}


async def get_user_create_back_menu(option):
    """
    Menu: Ozon Express management (User information)
    Level: 4.2.2
    Scheme: > (Back) > 3.2
    """
    markup = InlineKeyboardMarkup()

    markup.row(await create_button('Назад', ['user', '3', option, '0', '0', 'cancel']))

    return markup


# ****************************************Courier****************************************
async def open_courier_start_menu(cll: CallbackQuery, dp: Dispatcher):
    """
    Menu: Main
    Level: 2
    """
    markup = InlineKeyboardMarkup()
    callback = cll.data.split(':')

    await check_action_start_menu(callback, cll, dp)

    count = await db_query(func='fetch',
                           sql="""SELECT count(posting_number) FROM order_info 
                                          WHERE status = $2 AND warehouse_id IN (SELECT warehouse_id FROM employee 
                                                                                 WHERE tg_id = $1);""",
                           kwargs=[cll.from_user.id, 'awaiting_deliver'])

    orders_info = fmt.text("Доступно заказов:", fmt.hbold(count[0][0]["count"]))

    if count[0][0]["count"] != 0:
        info_text = fmt.text("\nНажмите ", fmt.hbold("Взять заказ"), " ,чтобы перейти к выбору")
        markup.row(await create_button("Назад", ['order', "2", "0", "0", "0", "back"]),
                   await create_button("Взять заказ", ["delivery", "3", "0", "0", "0", "open"]))

    else:
        info_text = fmt.text("\nНажмите ", fmt.hbold("Обновить"), "через несколько секунд")
        markup.row(await create_button("Назад", ["order", "2", "0", "0", "0", "back"]),
                   await create_button("Обновить", ["delivery", "2", "0", "0", "0", "update"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, orders_info, info_text, sep="\n")}


async def get_courier_order_menu(tg_id: int):
    """
    Menu: Orders management (Orders list)
    Level: 3
    """
    markup = InlineKeyboardMarkup()

    orders_data = await db_query(func='fetch',
                                 sql="""SELECT posting_number, latitude, longitude FROM order_info 
                                                WHERE status = $2 AND warehouse_id IN (SELECT warehouse_id FROM employee 
                                                                                       WHERE tg_id = $1)
                                                ORDER BY shipment_date;""",
                                 kwargs=[tg_id, 'awaiting_deliver'])
    # Заменить
    sorted_orders = await orders.get_similar_orders(orders_data[0][0], orders_data[0])

    final_orders = await db_query(func='fetch',
                                  sql="""WITH updated AS (UPDATE order_info SET status = $3, deliver_id = $2 
                                                                  WHERE posting_number = ANY($1) RETURNING *)
                                                 SELECT posting_number, address, shipment_date FROM updated 
                                                 WHERE status = $3 AND warehouse_id IN (SELECT warehouse_id 
                                                                                        FROM employee WHERE tg_id = $2)
                                                 ORDER BY shipment_date;""",
                                  kwargs=[tuple([order['posting_number'] for order in sorted_orders]),
                                          tg_id, 'reserved_by_deliver'])

    orders_data = final_orders[0]

    orders_info = fmt.text("Доступно заказов: ", fmt.hbold(len(orders_data)))
    info_text = fmt.text("\nОтметив заказ(ы), нажмите ", fmt.hbold("Подтвердить"), ", чтобы начать доставку")

    for ind, order in enumerate(orders_data):
        if ind == 0:
            markup.row(await create_button(order["posting_number"], ["delivery", "4", "0", "0",
                                                                     order["posting_number"], "open"]),
                       await create_button("✅️", ["delivery", "4", "0", "0", order["posting_number"], "added"]))
        else:
            markup.row(await create_button(order["posting_number"], ["delivery", "4", "0", "0",
                                                                     order["posting_number"], "open"]),
                       await create_button("☑️️", ["delivery", "4", "0", "0", order["posting_number"], "add"]))

    markup.row(await create_button("Отмена", ["delivery", "2", "0", "0", "0", "back"]),
               await create_button("Подтвердить", ["delivery", "5", "0", "0", "0", "open"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, orders_info, info_text, sep="\n")}


async def get_courier_order_info_menu(cll: CallbackQuery = None, state=None):
    """
    Menu: Orders management (Orders list)
    Level: 4
    """
    if cll:
        await extra.save_previous(cll.message.html_text, cll.message.reply_markup, state, first=True)

        markup = InlineKeyboardMarkup()

        order = await db_query(func='fetch',
                               sql="""SELECT posting_number, address, shipment_date, latitude, longitude
                                              FROM order_info WHERE posting_number = $1 AND status = $2;""",
                               kwargs=[cll.data.split(":")[-2], 'reserved_by_deliver'])
        order = order[0][0]
        orders_info = fmt.text(fmt.text(fmt.hbold("\nНомер отправления: "), fmt.text(order["posting_number"])),
                               fmt.text(fmt.hbold("Время доставки: "), fmt.text(order["shipment_date"])),
                               fmt.text(fmt.hbold("\nАдрес: "), fmt.hlink(order["address"],
                                                                          await extra.get_map_url(order["latitude"],
                                                                                                  order["longitude"]))),
                               sep="\n")

        markup.row(await create_button("Назад", ["delivery", "4", "0", "0", "0", "back"]))

        return {"reply_markup": markup, "text": fmt.text(menu_name, orders_info, sep="\n")}

    else:
        return await extra.save_previous(state=state, get=True, last=True, menu=True)


async def get_courier_order_select_menu(cll: CallbackQuery):
    """
    Menu: Orders management (Orders list)
    Level: 4
    """
    markup = cll.message.reply_markup

    for ind, button in enumerate(markup.inline_keyboard):
        if cll.data == button[1].callback_data:
            new_data = cll.data.split(":")

            if new_data[-1] == "add":
                new_sign, new_data[-1] = "✅️", "rem"

            elif new_data[-1] == "rem":
                new_sign, new_data[-1] = "☑️️", "add"

            else:
                continue

            markup.inline_keyboard[ind][1].text = new_sign
            markup.inline_keyboard[ind][1].callback_data = ":".join(new_data)

    return {"reply_markup": markup}


async def get_courier_delivering_menu(cll: CallbackQuery, state, dp: Dispatcher, tz):
    """
    Menu: Orders management (Orders list)
    Level: 5
    """
    markup = InlineKeyboardMarkup()
    info_text = fmt.text(fmt.text(fmt.hbold("Статус: "), "получение"),
                         fmt.text("Необходимо забрать товары со склада"),
                         sep="\n\n")

    added_orders, other_orders = [], []
    for ind, button in enumerate(cll.message.reply_markup.inline_keyboard):
        if ind + 1 != len(markup.inline_keyboard):
            if button[1].callback_data.split(":")[-1] in ["added", "rem"]:
                added_orders.append(button[0].text)

            else:
                other_orders.append(button[0].text)

    orders_for_delivery = await db_query(func='fetch',
                                         sql="""WITH updated AS (UPDATE order_info 
                                                                         SET status = $3, start_delivery_date = $4 
                                                                         WHERE posting_number = ANY($1) 
                                                                         AND deliver_id = $2 
                                                                         RETURNING *)
                                                        SELECT order_id, posting_number, address, addressee_name, 
                                                               addressee_phone, customer_comment, shipment_date, 
                                                               latitude, longitude
                                                        FROM updated WHERE status = $3 
                                                        AND warehouse_id IN (SELECT warehouse_id FROM employee 
                                                                             WHERE tg_id = $2);""",
                                         kwargs=[tuple(added_orders), cll.from_user.id, 'delivering',
                                                 (await get_time(tz=tz)).replace(tzinfo=None)])

    list_of_orders = [order["posting_number"] for order in orders_for_delivery[0]]
    await start_delivery(cll.from_user.id, list_of_orders)
    await send_info_log(dp, cll, "Начал доставку",
                        fmt.text(fmt.hbold("Номера отправлений: "), fmt.hcode(*list_of_orders)))

    await extra.save_previous(data_new=[dict(order) for order in orders_for_delivery[0]], first=True, state=state)

    if other_orders:
        await db_query(func='fetch',
                       sql="""WITH updated AS (UPDATE order_info SET status = $3, deliver_id = $4 
                                                       WHERE status = $2 AND deliver_id = $1 RETURNING *)
                                      SELECT count(posting_number) FROM updated WHERE status = $3 
                                      AND warehouse_id IN (SELECT warehouse_id FROM employee WHERE tg_id = $1);""",
                       kwargs=[cll.from_user.id, 'reserved_by_deliver', 'awaiting_deliver', None])

    for ind, order in enumerate(orders_for_delivery[0]):
        markup.row(await create_button(order["posting_number"],
                                       ["delivery", "6", "in_process", ind, order["posting_number"], "open"]))

    markup.row(await create_button("Забрал со склада", ["delivery", "7", "0", "0", "0", "open"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, info_text, sep="\n")}


async def get_courier_delivering_order_info(cll: CallbackQuery = None, state=None):
    """
    Menu: Orders management (Orders list)
    Level: 6
    """
    if cll:
        markup = InlineKeyboardMarkup()

        await extra.save_previous(cll.message.html_text, cll.message.reply_markup, state=state)
        order, option = await extra.save_previous(state=state, get=True), cll.data.split(":")

        orders_info = fmt.text(fmt.text(fmt.hbold("\nНомер отправления: "),
                                        fmt.text(order[int(option[4])]["posting_number"])),
                               fmt.text(fmt.hbold("Время доставки: "),
                                        str(order[int(option[4])]["shipment_date"])),
                               fmt.text(fmt.hbold("\nАдрес: "), fmt.hlink(order[int(option[4])]["address"],
                                                                          await extra.get_map_url(
                                                                              order[int(option[4])]["latitude"],
                                                                              order[int(option[4])]["longitude"]))),
                               fmt.text(fmt.hbold("\nПолучатель: "), (order[int(option[4])]['addressee_name'])),
                               fmt.text(fmt.hbold("Телефон: "),
                                        fmt.hcode(f"+{order[int(option[4])]['addressee_phone']}")),
                               fmt.text(fmt.hbold("\nКоментарий: "), order[int(option[4])]['customer_comment']),
                               sep='\n')

        markup.row(await create_button("Назад", ["delivery", "6", "0", "0", "0", "back"]))

        return {"reply_markup": markup, "text": fmt.text(menu_name, orders_info, sep="\n")}

    else:
        return await extra.save_previous(state=state, get=True, menu=True)


async def get_courier_delivering_menu_next(cll: CallbackQuery, state):
    """
    Menu: Orders management (Orders list)
    Level: 7
    """
    markup = InlineKeyboardMarkup()

    orders_for_delivery = await extra.save_previous(state=state, get=True)
    list_of_orders = [order["posting_number"] for order in orders_for_delivery]
    await start_delivery_last_mile(cll.from_user.id, list_of_orders)

    info_text = fmt.text(fmt.text(fmt.hbold("Статус: "), "в процессе"),
                         fmt.text(fmt.hbold("Прогресс: "), fmt.hbold("0"),
                                  " из ", fmt.hbold(f"{len(orders_for_delivery)}")),
                         sep="\n")

    for ind, order in enumerate(orders_for_delivery):
        markup.row(await create_button(order["posting_number"], ["delivery", "6", "in_process", ind,
                                                                 order["posting_number"], "open"]))
        markup.row(await create_button("✖Не доставлен", ["delivery", "7", "button", "0",
                                                         order["posting_number"], "undelivered"]),
                   await create_button("✔Доставлен", ["delivery", "7", "button", "0",
                                                      order["posting_number"], "delivered"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, info_text, sep="\n")}


async def get_courier_result_delivering_menu(cll: CallbackQuery, dp: Dispatcher, tz):
    """
    Menu: Orders management (Orders list)
    Level: 7
    """

    markup = InlineKeyboardMarkup()
    callback, in_process, delivered, undelivered = cll.data.split(":"), 0, 0, 0

    for row in cll.message.reply_markup.inline_keyboard:
        if len(row) == 1:
            for button in row:
                button_data = button.callback_data.split(":")

                if callback[-2] == button_data[-2]:
                    if callback[-1] == "undelivered":
                        markup.row(await create_button(f"{button.text} 😔",
                                                       ["delivery", "6", "cancel", button_data[-3],
                                                        button_data[-2], "open"]))
                        markup.row(await create_button(f"🔙Отказ от товара",
                                                       ["delivery", "7", "button", button_data[-3],
                                                        button_data[-2], "return"]),
                                   await create_button(f"📵Не дозвонился",
                                                       ["delivery", "7", "button", button_data[-3],
                                                        button_data[-2], "no_call"]))
                        in_process += 1

                    elif callback[-1] == "delivered":
                        markup.row(await create_button(f"{button.text} 😁",
                                                       ["delivery", "6", "delivered", button_data[-3],
                                                        button_data[-2], "open"]))
                        await complete_delivery_ozon(cll.from_user.id, button.text)
                        await db_query(func='execute',
                                       sql="""WITH updated AS (UPDATE order_info 
                                                                       SET status = $2, finish_delivery_date = $3 
                                                                       WHERE posting_number = $1 RETURNING *)
                                                      INSERT INTO logs_status_changes
                                                      (date, status, status_ozon_seller, posting_number)
                                                      VALUES($3, $2, $4, $1);""",
                                       kwargs=[button_data[-2], 'delivered',
                                               (await get_time(tz=tz)).replace(tzinfo=None), 'delivering'])
                        await send_info_log(dp, cll, "Завершил заказ",
                                            fmt.text(fmt.text(fmt.hbold("Номер отправления: "), button.text),
                                                     fmt.text(fmt.hbold("Статус: "), "Доставлено"),
                                                     sep="\n"))
                        delivered += 1

                    elif callback[-1] in ["return", "no_call"]:
                        markup.row(await create_button(
                            f"{button.text} 📵" if callback[-1] == "no_call" else f"{button.text} 🔙",
                            ["delivery", "6", "undelivered", button_data[-3], button_data[-2], "open"]))
                        reason = "Отказ" if callback[-1] == "return" else "Не дозвонился"

                        await db_query(func='execute',
                                       sql="""WITH updated AS (UPDATE order_info 
                                                                       SET status = $2, finish_delivery_date = $3 
                                                                       WHERE posting_number = $1 RETURNING *)
                                                      INSERT INTO logs_status_changes
                                                      (date, status, status_ozon_seller, posting_number)
                                                      VALUES($3, $2, $4, $1);""",
                                       kwargs=[button_data[-2], 'undelivered',
                                               (await get_time(tz=tz)).replace(tzinfo=None), 'delivering'])
                        await send_info_log(dp, cll, "Завершил заказ",
                                            fmt.text(fmt.text(fmt.hbold("Номер отправления: "), button.text[:-1]),
                                                     fmt.text(fmt.hbold("Статус: "), "Не доставлено"),
                                                     fmt.text(fmt.hbold("Причина: "), reason),
                                                     sep="\n"))
                        undelivered += 1

                elif button_data[3] == "in_process":
                    markup.row(await create_button(button.text,
                                                   ["delivery", "6", "in_process", button_data[-3],
                                                    button_data[-2], "open"]))
                    markup.row(await create_button("✖Не доставлен", ["delivery", "7", "button", button_data[-3],
                                                                     button_data[-2], "undelivered"]),
                               await create_button("✔Доставлен", ["delivery", "7", "button", button_data[-3],
                                                                  button_data[-2], "delivered"]))
                    in_process += 1

                elif button_data[3] == "cancel":
                    markup.row(await create_button(button.text, ["delivery", "6", "cancel", button_data[-3],
                                                                 button_data[-2], "open"]))
                    markup.row(
                        await create_button(f"🔙Отказ от товара",
                                            ["delivery", "7", "button", button_data[-3], button_data[-2], "return"]),
                        await create_button(f"📵Не дозвонился",
                                            ["delivery", "7", "button", button_data[-3], button_data[-2], "no_call"]))
                    in_process += 1

                elif button_data[3] == "delivered":
                    markup.row(await create_button(button.text, ["delivery", "6", "delivered", button_data[-3],
                                                                 button_data[-2], "open"]))
                    delivered += 1

                elif button_data[3] == "undelivered":
                    markup.row(await create_button(button.text, ["delivery", "6", "undelivered", button_data[-3],
                                                                 button_data[-2], "open"]))
                    undelivered += 1

                break

    if in_process == 0:
        if undelivered == 0:
            final_msg = fmt.text("\nОтлично! Вы доставили все заказы🥳\n")
            markup.row(await create_button("Возвращаюсь на склад",
                                           ["delivery", "8", "returning", "0", "0", "open"]))
            await finish_state(cll.message.chat.id, cll.from_user.id)

        else:
            final_msg = fmt.text(fmt.text("\nВы завершили доставку🙂\n"),
                                 fmt.text("Не забудьте вернуть недоставленный товар на склад😉\n"))
            markup.row(await create_button("Возвращаюсь на склад",
                                           ["delivery", "8", "returning", "undelivered", "0", "open"]))
        final_info_text = fmt.text("Нажмите кнопку ", fmt.hbold("Возвращаюсь на склад"),
                                   ", чтобы завершить доставку")
        status = "завершено"
    else:
        final_msg, final_info_text, status = fmt.text(""), fmt.text(""), "доставка"

    total_count = in_process + delivered + undelivered
    info_text = fmt.text(fmt.text(fmt.hbold("Статус: "), status),
                         fmt.text(fmt.hbold("Прогресс: "), fmt.hbold(total_count - in_process),
                                  " из ", fmt.hbold(total_count)),
                         sep="\n")

    return {"reply_markup": markup, "text": fmt.text(menu_name, info_text, final_msg, final_info_text, sep="\n")}


async def get_courier_complete_delivery_menu(cll: CallbackQuery):
    """
    Menu: Orders management (Orders list)
    Level: 8
    """
    markup = InlineKeyboardMarkup()
    await finish_state(cll.from_user.id, cll.from_user.id)

    if cll.data.split(":")[-3] == "undelivered":
        info_text = fmt.text(fmt.text(fmt.hbold("Статус: "), "Завершено"),
                             fmt.text("После передачи товара на склад, нажмите кнопку ниже, для выхода в главное меню"),
                             sep="\n")

        markup.row(await create_button("Вернул заказ на склад", ["delivery", "2", "0", "0", "0", "finish"]))
    else:
        info_text = fmt.text(fmt.text(fmt.hbold("Статус: "), "Завершено"),
                             fmt.text("\nДля выхода в главное меню, нажмите кнопку ниже"),
                             sep="\n")

        markup.row(await create_button("Вернулся на склад", ["delivery", "2", "0", "0", "0", "finish"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, info_text, sep="\n")}


# ****************************************Packer****************************************
async def open_packer_start_menu(cll: CallbackQuery, dp: Dispatcher, tz: str):
    markup = InlineKeyboardMarkup()

    await check_action_start_menu(cll.data.split(":"), cll, dp, tz)

    count = await db_query(func='fetch',
                           sql="""SELECT count(posting_number) FROM order_info 
                                          WHERE status = $2 AND warehouse_id IN (SELECT warehouse_id FROM employee 
                                                                                 WHERE tg_id = $1);""",
                           kwargs=[cll.from_user.id, "awaiting_packaging"])
    orders_info = fmt.text("Доступно заказов: ", fmt.hbold(count[0][0]["count"]))

    if count[0][0]["count"] != 0:
        info_text = fmt.text("\nНажмите ", fmt.hbold("Собрать заказ"), " ,чтобы перейти к выбору")
        markup.row(await create_button("Назад", ["order", "2", "0", "0", "0", "open"]),
                   await create_button("Собрать заказ", ["package", "3", "0", "0", "0", "open"]))
    else:
        info_text = fmt.text("\nНажмите ", fmt.hbold("Обновить"), "через несколько секунд")
        markup.row(await create_button("Назад", ["order", "2", "0", "0", "0", "open"]),
                   await create_button("Обновить", ["package", "2", "0", "0", "0", "update"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, orders_info, info_text, sep="\n")}


async def open_packer_orders_menu(cll: CallbackQuery, state, action: str):
    markup = InlineKeyboardMarkup()

    if action == "open":
        orders_data = await db_query(func='fetch',
                                     sql="""WITH updated AS (UPDATE order_info SET status = $3, packer_id = $1
                                                                     WHERE status = $2 
                                                                     AND warehouse_id IN (SELECT warehouse_id 
                                                                                          FROM employee 
                                                                                          WHERE tg_id = $1) 
                                                                     RETURNING *)
                                                    SELECT u.posting_number, u.address, u.shipment_date, 
                                                    u.in_process_at, u.latitude, u.longitude, u.customer_name, 
                                                    u.customer_phone, u.customer_comment, count(o.name), sum(o.quantity)
                                                    FROM updated u, order_list o 
                                                    WHERE u.posting_number = o.posting_number AND u.status = $3
                                                    AND u.warehouse_id IN (SELECT warehouse_id FROM employee 
                                                                           WHERE tg_id = $1)
                                                    GROUP BY (u.posting_number, u.address, u.shipment_date, 
                                                              u.in_process_at, u.latitude, u.longitude, u.customer_name, 
                                                              u.customer_phone, u.customer_comment)
                                                    ORDER BY u.shipment_date;""",
                                     kwargs=[cll.from_user.id, 'awaiting_packaging', 'reserved_by_packer'])
        orders_data = orders_data[0]
    else:
        orders_data = await extra.save_previous(state=state, get=True)

    info_text = fmt.text("\nДоступно заказов: ", fmt.hbold(len(orders_data)))

    await extra.save_previous(data_new=[dict(order) for order in orders_data], first=True, state=state)

    order_info = []
    for ind, order in enumerate(orders_data):
        order_info.append(fmt.text(fmt.text(fmt.hbold(f"\nЗаказ №{ind + 1}")),
                                   fmt.text(fmt.hbold("Номер отправления: "), order["posting_number"]),
                                   fmt.text(fmt.hbold("Товаров: "), order["sum"]),
                                   fmt.text(fmt.hbold("Адрес: "),
                                            fmt.hlink(order["address"], await extra.get_map_url(order["latitude"],
                                                                                                order["longitude"]))),
                                   sep="\n"))

        markup.row(await create_button(f"\nЗаказ №{ind + 1}\n",
                                       ["package", "4", ind, "0", order["posting_number"], "open"]))

    markup.row(await create_button("Назад", ["package", "2", "0", "0", "0", "back"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, info_text, *order_info, sep="\n")}


async def get_packer_order_menu(callback, state):
    markup = InlineKeyboardMarkup()

    order_data = await extra.save_previous(state=state, get=True)
    order = order_data[int(callback["option"])]

    order_info = fmt.text(fmt.text(fmt.hbold("Номер отправления: "), order["posting_number"]),
                          fmt.text(fmt.hbold("\nВремя создания: "), order["in_process_at"]),
                          fmt.text(fmt.hbold("Время доставки"), order["shipment_date"]),
                          fmt.text(fmt.hbold("\nПокупатель: "), fmt.hitalic(order["customer_name"])),
                          fmt.text(fmt.hbold("Тел. покупателя:"), fmt.hcode(f"+{order['customer_phone']}")),
                          fmt.text(fmt.hbold("Коментарий: "), order["customer_comment"]),
                          fmt.text(fmt.hbold("\nАдрес: "), fmt.hlink(order["address"],
                                                                     await extra.get_map_url(order["latitude"],
                                                                                             order["longitude"]))),
                          fmt.text(fmt.hbold("\nПозиций: "), order["count"]),
                          fmt.text(fmt.hbold("Товаров: "), order["sum"]),
                          sep="\n")

    markup.row(await create_button("Назад", ["package", "3", "0", "0", "0", "back"]),
               await create_button("Сборка", ["package", "5", "0", "0", callback["item_id"], "open"]))

    return {"reply_markup": markup, "text": fmt.text(menu_name, order_info, sep="\n")}


async def get_packer_package_order_menu(callback, cll: CallbackQuery, dp: Dispatcher, tz: str):
    markup = InlineKeyboardMarkup()

    if callback["action"] == "open":
        await db_query(func='execute',
                       sql="""WITH updated AS (UPDATE order_info SET status = $3, start_package_date = $7
                                                       WHERE posting_number = $1 RETURNING *)
                                      UPDATE order_info SET status = $4, packer_id = $6 WHERE status = $2 
                                      AND packer_id = $5 AND posting_number != $1;""",
                       kwargs=[callback["item_id"], 'reserved_by_packer', "packaging",
                               'awaiting_packaging', cll.from_user.id, None,
                               (await get_time(tz=tz)).replace(tzinfo=None)])
        await send_info_log(dp, cll, "Начал сборку", fmt.text(fmt.hbold("Заказ: "), fmt.hcode(callback["item_id"])))

    order_info = await db_query(func='fetch',
                                sql="""SELECT * FROM order_list WHERE posting_number = $1 ORDER BY name;""",
                                kwargs=[callback["item_id"]])

    for ind, order in enumerate(order_info[0]):
        fact_quantity = order["fact_quantity"]
        if int(callback["option"]) == order["sku"]:
            if callback["action"] == "minus":
                print(order)
                if fact_quantity != 0:
                    fact_quantity -= 1

            elif callback["action"] == "plus":
                if fact_quantity < order["quantity"]:
                    fact_quantity += 1

            await db_query(func='execute',
                           sql="""UPDATE order_list SET fact_quantity = $2 
                                          WHERE name = $1 AND posting_number = $3;""",
                           kwargs=[order["name"], fact_quantity, callback["item_id"]])

        more = f"{order['quantity']} -> " if order["quantity"] < fact_quantity else ""
        less = f" <- {order['quantity']}" if order["quantity"] > fact_quantity else ""

        markup.row(await create_button(f"{ind + 1}. {order['name']}", ["package", "6", order["sku"], "0",
                                                                       callback["item_id"], "open"]))
        markup.row(await create_button("-", ["package", "5", order["sku"], "0", callback["item_id"], "minus"]),
                   await create_button(f"{more}{fact_quantity}{less}", ["order", "4", order["sku"], "0",
                                                                                 callback["item_id"], "pass"]),
                   await create_button("+", ["package", "5", order["sku"], "0", callback["item_id"], "plus"]))
    markup.row(await create_button("Отменить", ["package", "6", "0", "0", callback["item_id"], "cancel"]),
               await create_button("Собран", ["package", "7", "0", "0", callback["item_id"], "complete"]))

    return {"reply_markup": markup}


async def get_packer_product_id_menu(cll: CallbackQuery = None, state=None):
    if cll:
        await extra.save_previous(cll.message.html_text, cll.message.reply_markup, state=state)

        markup = InlineKeyboardMarkup()

        info = await get_info(cll.from_user.id, int(cll.data.split(":")[-4]))
        order_info = fmt.text(fmt.hbold("\nШтрих-код: "), info["barcode"], fmt.hide_link(info["primary_image"]))

        markup.row(await create_button("Назад", ["package", "6", "0", "0", cll.data.split(":")[-2], "back"]))

        return {"reply_markup": markup, "text": fmt.text(menu_name, order_info, sep="\n")}

    else:
        return await extra.save_previous(state=state, get=True, menu=True)


async def get_packer_reasons_for_cancel_menu(cll: CallbackQuery = None, state=None):
    if cll:
        await extra.save_previous(cll.message.html_text, cll.message.reply_markup, state=state)

        markup = InlineKeyboardMarkup()

        order_info = fmt.text(fmt.text(f"\nОтмена заказа", fmt.hbold(cll.data.split(":")[-2])),
                              fmt.text("\nВыберете причину или введите свою, нажав ", fmt.hbold("Другая причина")),
                              sep="\n")

        for key, item in CANCELLATION_STATUS.items():
            if key == 402:
                markup.row(await create_button(item.capitalize(),
                                               ["package", "6", key, "0", cll.data.split(":")[-2], "future"]))
            else:
                markup.row(await create_button(item.capitalize(),
                                               ["package", "3", key, "0", cll.data.split(":")[-2], "cancel"]))

        markup.row(await create_button("Назад", ["package", "6", "0", "0", cll.data.split(":")[-2], "back"]))

        return {"reply_markup": markup, "text": fmt.text(menu_name, order_info, sep="\n")}

    else:
        return await extra.save_previous(state=state, get=True, menu=True)


async def get_packer_complete_menu(cll: CallbackQuery, dp: Dispatcher, state, tz: str):
    markup = InlineKeyboardMarkup()

    order_info = await db_query(func='fetch',
                                sql="""SELECT * FROM order_list WHERE posting_number = $1 ORDER BY name;""",
                                kwargs=[cll.data.split(":")[-2]])

    status, posting_number = await complete_packaging_ozon(order_info[0], cll.from_user.id)

    info_text = fmt.text(f"\nПоздравляем! Вы успешно завершили сборку заказа", fmt.hbold(posting_number))

    markup.row(await create_button("Готово", ["package", "2", "0", "0", "0", "back"]))

    await extra.check_state(state)
    await send_info_log(dp, cll, "завершил сборку",
                        fmt.text(fmt.text(fmt.hbold("Заказ: "),
                                          fmt.hcode(posting_number)),
                                 fmt.text(fmt.hbold("\nСобран: "), "Частично" if status else "Полностью")))

    if status:
        await db_query(func="execute",
                       sql="""WITH updated AS (UPDATE order_info 
                                                       SET status = $2, finish_package_date = $3, 
                                                       cancel_reason_id = $5, cancel_reason = $6, 
                                                       cancellation_type = $7, cancellation_initiator = $8
                                                       WHERE posting_number = $1 RETURNING *)
                                      INSERT INTO logs_status_changes (date, status, status_ozon_seller, posting_number)
                                      VALUES($3, $2, $4, $1);""",
                       kwargs=[cll.data.split(":")[-2], "canceled", (await get_time(tz=tz)).replace(tzinfo=None),
                               "canceled", 352, CANCELLATION_STATUS[352], "seller",
                               "Продавец"])
    else:
        await db_query(func='execute',
                       sql="""WITH updated AS (UPDATE order_info SET status = $2, finish_package_date = $3
                                                       WHERE posting_number = $1 RETURNING *)
                                      INSERT INTO logs_status_changes (date, status, status_ozon_seller, posting_number)
                                      VALUES($3, $2, $4, $1);""",
                       kwargs=[cll.data.split(":")[-2], 'awaiting_deliver',
                               (await get_time(tz=tz)).replace(tzinfo=None), 'awaiting_deliver'])

    return {"reply_markup": markup, "text": fmt.text(menu_name, info_text, sep="\n")}
