from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData

from utils.db import sql
from data.condition import FUNCTION


async def get_callback(function_: str, args: list) -> str:
    if function_ in ["creator", "moderator"]:
        return CallbackData(function_, "menu", "level", "seller", "option", "item", "item_id", "action").new(*args)
    else:
        return CallbackData(function_, "menu", "level", "option", "item", "item_id", "action").new(*args)


async def create_btn(function_: str, name_: str,  args: list) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=name_, callback_data=await get_callback(function_, args))


# ****************************************InlineKeyboard****************************************
async def create_inline_keyboard(function: str, lst_of_rows: list) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    for row in lst_of_rows:
        markup.row(*[await create_btn(function, item[0], item[1]) for item in row.items()])
    return markup


# ****************************************ReplyKeyboard****************************************
async def create_reply_keyboard(lst_of_rows: list) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for row in lst_of_rows:
        buttons = []
        for args in row:
            buttons.append(KeyboardButton(args[0], request_location=False if len(args) == 1 else args[1]))
        markup.row(*buttons)
    return markup


# ****************************************ReplyMarkupData****************************************
async def create_reply_markup(text: str, buttons: InlineKeyboardMarkup) -> dict:
    return {"text": text, "reply_markup": buttons}


async def return_markup(markup: InlineKeyboardMarkup) -> dict:
    return {"reply_markup": markup}


class PackerButton:
    def __init__(self):
        self.on_shift_statuses = ["on_shift", "reserve_package", "packaging"]
        self.fact_quantity = 0

    async def buttons_1(self, function: str, status: str) -> InlineKeyboardMarkup:
        if status in self.on_shift_statuses:
            buttons = [{"Сборка отправления": ["package", "2", "0", "0", "0", "open"]},
                       {"Информация": ["info", "1", "0", "0", "0", "open"]},
                       {"Завершить смену": ["main", "1", "0", "0", "0", "finish"]}]
        else:
            buttons = [{"Начать смену": ["main", "1", "0", "0", "0", "start"]},
                       {"Информация": ["info", "1", "0", "0", "0", "open"]},
                       {"Выйти": ["main", "0", "0", "0", "0", "close_bot"]}]
        return await create_inline_keyboard(function, buttons)

    async def buttons_2(self, function: str, count: int) -> InlineKeyboardMarkup:
        buttons = []
        if count != 0:
            buttons.append({"Назад": await self.get_callback_data_2(function),
                            "Сборка": ["package", "3", "0", "0", "0", "reserve_package"]})
        else:
            buttons.append({"Назад": await self.get_callback_data_2(function),
                            "Обновить": ["package", "2", "0", "0", "0", "update"]})
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_3(function: str, orders: list) -> InlineKeyboardMarkup:
        buttons = [{f"Заказ №{ind + 1}": ["package", "4", ind, "0", order["posting_number"], "open"]}
                   for ind, order in enumerate(orders)]
        buttons.append(dict(Назад=["package", "2", "0", "0", "0", "reserve_back"]))
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_4(function: str, post_number_: str) -> InlineKeyboardMarkup:
        buttons = [{"Назад": ["package", "3", "0", "0", "0", "back"],
                    "Собрать": ["package", "5", "0", "0", post_number_, "start_packaging"]}]
        return await create_inline_keyboard(function, buttons)

    async def buttons_5(self, function: str, category_names: dict, products_info: dict,
                        post: str, obj: str, action: str) -> InlineKeyboardMarkup:
        buttons = []
        for key, value in category_names.items():
            if key == products_info["product_rank"]:
                name = f"️🔽 ({products_info['all_ranks'].count(key)}) ️️{value}️"
                buttons.append({name: ["package", "5", "category", key, post, "open"]})
                count = 0
                for index, product in enumerate(await sql.get_products_info(post)):
                    if int(key) == int(products_info["products"][str(product["sku"])]["rank"]):
                        await self.write_fact_quantity(product, action, obj, post)
                        product_quantity = await self.check_change_in_quantity(product["quantity"])
                        product_name = await self.format_product_name(count, product['name'])
                        weight = await self.get_product_weight(product["weight"])
                        buttons.append({f"{product_name}": ["package", "6", product["sku"], weight, post, "open"]})
                        buttons.append({"-": ["package", "5", product["sku"], weight, post, "minus"],
                                        product_quantity: ["package", "4", product["sku"], weight, post, "pass"],
                                        "+": ["package", "5", product["sku"], weight, post, "plus"]})
                        if weight != "0":
                            buttons[-1][f"{weight} гр"] = ["package", "9", product["sku"], weight, post, "start_weight"]
                        count += 1
            else:
                name = f"⏹ ️({products_info['all_ranks'].count(key)}) {value}"
                buttons.append({name: ["package", "5", "category", key, post, "open"]})
        buttons.append({"Отменить": ["package", "9", "0", "0", post, "start_cancel"],
                        "Собран": ["package", "7", "0", "0", post, "open"]})
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_6(function: str, post_: str, sku_: str) -> InlineKeyboardMarkup:
        buttons = [{"Назад": ["package", "5", "0", "0", post_, "back"],
                    "Ввести вес": ["package", "9", sku_, "0", post_, "start_weight"]}]
        return await create_inline_keyboard(function, buttons)

    async def buttons_7(self, function: str, post_: str, action: str) -> InlineKeyboardMarkup:
        list_action, action_name = await self.check_roll(action)
        buttons = [{action_name:   ["package", "7", "0", "0", post_, list_action]},
                   {"Назад":       ["package", "7", "0", "0", post_, "back"],
                    "Подтвердить": ["package", "8", "0", "0", post_, "confirm"]}]
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_8(function: str) -> InlineKeyboardMarkup:
        buttons = [{"Готово": ["package", "2", "0", "0", "0", "complete"]}]
        return await create_inline_keyboard(function, buttons)

    async def update_product_quantity(self, product: dict, action: str, sku: int, posting_number):
        self.fact_quantity = product["fact_quantity"]
        if sku == product["sku"]:
            if (action == "minus") and (self.fact_quantity != 0):
                self.fact_quantity -= 1
            elif (action == "plus") and (self.fact_quantity < product["quantity"]):
                self.fact_quantity += 1
        await sql.update_product_fact_quantity(product["name"], self.fact_quantity, posting_number)
        return

    async def check_change_in_quantity(self, quantity):
        more = f"{quantity} -> " if quantity < self.fact_quantity else ""
        less = f" <- {quantity}" if quantity > self.fact_quantity else ""
        return f"{more}{self.fact_quantity}{less}"

    @staticmethod
    async def format_product_name(index, product_name: str):
        lst_product_name = product_name.split(', ')
        return f"{index + 1}. {lst_product_name[-1]}, {', '.join(lst_product_name[:-1])}"

    @staticmethod
    async def get_product_weight(weight):
        return str(weight) if weight else "0"

    async def write_fact_quantity(self, product, action, obj, post):
        sku = int(product["sku"]) if obj == "category" else int(obj)
        await self.update_product_quantity(dict(product), action, sku, post)

    @staticmethod
    async def check_roll(action_: str):
        return ("roll_down", "Свернуть") if action_ == "roll_up" else ("roll_up", "Развернуть")

    @staticmethod
    async def get_callback_data_2(function: str) -> list:
        return ["main", "1", "0", "0", "0", "back"] if function == 'packer' else ["order", "2", "0", "0", "0", "back"]


class DeliverButton:
    def __init__(self):
        self.on_shift_statuses = ["on_shift", "reserve_delivery", "delivering"]

    async def buttons_1(self, function: str, status: str) -> InlineKeyboardMarkup:
        if status in self.on_shift_statuses:
            buttons = [{"Доставка отправлений": ["delivery", "2", "0", "0", "0", "open"]},
                       {"Информация": ["info", "1", "0", "0", "0", "open"]},
                       {"Завершить смену": ["main", "1", "0", "0", "0", "finish"]}]
        else:
            buttons = [{"Начать смену": ["main", "1", "0", "0", "0", "start"]},
                       {"Информация": ["info", "1", "0", "0", "0", "open"]},
                       {"Выйти": ["main", "0", "0", "0", "0", "close_bot"]}]
        return await create_inline_keyboard(function, buttons)

    async def buttons_2(self, function: str, count: int) -> InlineKeyboardMarkup:
        if count != 0:
            buttons = [{"Назад": await self.get_callback_data_2(function),
                        "Доставка": ["delivery", "3", "0", "0", "0", "reserve_delivery"]}]
        else:
            buttons = [{"Назад": await self.get_callback_data_2(function),
                        "Обновить": ["delivery", "2", "0", "0", "0", "update"]}]
        return await create_inline_keyboard(function, buttons)

    async def buttons_3(self, function: str, orders: list, action: str) -> InlineKeyboardMarkup:
        buttons = [{order["posting_number"]: ["delivery", "4", "0", "0", order["posting_number"], "open"],
                    "☑️": ["delivery", "5", "0", "0", order["posting_number"], "add"]} for order in orders]
        buttons.append(await self.get_callback_data_3(action))
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_4(function: str) -> InlineKeyboardMarkup:
        buttons = [{"Назад": ["delivery", "4", "0", "0", "0", "back"]}]
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_5(cll: CallbackQuery) -> InlineKeyboardMarkup:
        markup = cll.message.reply_markup
        for ind, button in enumerate(markup.inline_keyboard):
            if cll.data == button[1].callback_data:
                new_data = cll.data.split(":")
                if new_data[6] in ["add", "rem"]:
                    new_sign, new_data[6] = ("✅️", "rem") if new_data[-1] == "add" else ("☑️️", "add")
                    markup.inline_keyboard[ind][1].text = new_sign
                    markup.inline_keyboard[ind][1].callback_data = ":".join(new_data)
                    break
        return markup

    async def buttons_6(self, function: str, orders: list = None) -> InlineKeyboardMarkup:
        if orders:
            buttons = [await self.get_callback_data_6(ind, order) for ind, order in enumerate(orders)]
            buttons.append({"Забрал со склада": ["delivery", "8", "0", "0", "0", "open"]})
            if len(orders) <= 4:
                buttons.insert(0, {"Добавить отправления": ["delivery", "3", 5 - len(orders), "0", "0", "ex_add"]})
        else:
            buttons = [{"Вернуться": ["main", "1", "0", "0", "0", "back"]}]
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_7(function: str) -> InlineKeyboardMarkup:
        buttons = [{"Назад": ["delivery", "7", "0", "0", "0", "back"]}]
        return await create_inline_keyboard(function, buttons)

    async def buttons_8(self, function: str, orders: list) -> InlineKeyboardMarkup:
        buttons = []
        [buttons.extend(await self.get_callback_data_8(ind, order)) for ind, order in enumerate(orders)]
        return await create_inline_keyboard(function, buttons)

    async def buttons_9(self, function: str, callback: list, markup: InlineKeyboardMarkup
                        ) -> (InlineKeyboardMarkup, int, int, int):
        in_process, delivered, undelivered, buttons = 0, 0, 0, []

        for button in [row[0] for row in markup.inline_keyboard if len(row) == 1]:
            button_data = button.callback_data.split(":")

            if callback[5] == button_data[5]:
                buttons.extend(await self.get_callback_data_9_1(callback))
                if callback[6] in ["undelivered", "back"]:
                    in_process += 1
                elif callback[6] == "delivered":
                    delivered += 1
                elif callback[6] in ["return", "no_call"]:
                    undelivered += 1
            else:
                buttons.extend(await self.get_callback_data_9_2(button.text, button_data))
                if button_data[3] in ["in_process", "cancel"]:
                    in_process += 1
                elif button_data[3] == "delivered":
                    delivered += 1
                elif button_data[3] == "undelivered":
                    undelivered += 1

        if in_process == 0:
            buttons.append({"Возвращаюсь на склад": ["delivery", "10", "returning",
                                                     "0" if undelivered == 0 else "undelivered", "0", "open"]})

        return await create_inline_keyboard(function, buttons), in_process, delivered, undelivered

    @staticmethod
    async def buttons_10(function: str, consist: str) -> InlineKeyboardMarkup:
        buttons = [{"Вернул заказ на склад" if consist == "undelivered"
                    else "Вернулся на склад": ["delivery", "2", "0", "0", "0", "complete"]}]
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def get_callback_data_2(function: str) -> list:
        return ["main", "1", "0", "0", "0", "back"] if function == 'courier' else ["order", "2", "0", "0", "0", "back"]

    @staticmethod
    async def get_callback_data_3(action: str) -> dict:
        if action == "ex_add":
            return {"Отмена": ["delivery", "6", "0", "0", "0", "ex_reserve_back"],
                    "Подтвердить": ["delivery", "6", "0", "0", "0", "ex_reserve_delivery"]}
        else:
            return {"Отмена": ["delivery", "2", "0", "0", "0", "reserve_back"],
                    "Подтвердить": ["delivery", "6", "0", "0", "0", "reserve_delivery"]}

    @staticmethod
    async def get_callback_data_6(ind: int, order: dict) -> dict:
        return {order["posting_number"]: ["delivery", "7", "in_process", ind, order["posting_number"], "open"]}

    @staticmethod
    async def get_callback_data_8(ind: int, order: dict) -> list:
        main_button = {order["posting_number"]: ["delivery", "7", "in_process", ind, order["posting_number"], "open"]}
        ex_button = {"✖Не доставлен": ["delivery", "9", "button", "0", order["posting_number"], "undelivered"],
                     "✔Доставлен": ["delivery", "9", "button", "0", order["posting_number"], "delivered"]}
        return [main_button, ex_button]

    @staticmethod
    async def get_callback_data_9_1(callback: list) -> list:
        data = {"undelivered": [{callback[5]: ["delivery", "7", "cancel", callback[4], callback[5], "open"]},
                                {"Назад": ["delivery", "9", "button", callback[4], callback[5], "back"],
                                 "🔙Отказ от товара": ["delivery", "9", "button", callback[4], callback[5], "return"],
                                 "📵Не дозвонился": ["delivery", "9", "button", callback[4], callback[5], "no_call"]}],
                "delivered": [{f"{callback[5]} ✅": ["delivery", "7", "delivered", callback[4], callback[5], "open"]}],
                "return": [{f"{callback[5]} 🔙": ["delivery", "7", "undelivered", callback[4], callback[5], "open"]}],
                "no_call": [{f"{callback[5]} 📵": ["delivery", "7", "undelivered", callback[4], callback[5], "open"]}],
                "back": [{callback[5]: ["delivery", "7", "in_process", callback[4], callback[5], "open"]},
                         {"✖Не доставлен": ["delivery", "9", "button", callback[4], callback[5], "undelivered"],
                          "✔Доставлен": ["delivery", "9", "button", callback[4], callback[5], "delivered"]}]}
        return data[callback[6]]

    @staticmethod
    async def get_callback_data_9_2(post: str, callback: list) -> list:
        data = {"in_process": [{post: ["delivery", "7", "in_process", callback[4], callback[5], "open"]},
                               {"✖Не доставлен": ["delivery", "9", "button", callback[4], callback[5], "undelivered"],
                                "✔Доставлен": ["delivery", "9", "button", callback[4], callback[5], "delivered"]}],
                "cancel": [{post: ["delivery", "7", "cancel", callback[4], callback[5], "open"]},
                           {"Назад": ["delivery", "9", "button", callback[4], callback[5], "back"],
                            "🔙Отказ от товара": ["delivery", "9", "button", callback[4], callback[5], "return"],
                            "📵Не дозвонился": ["delivery", "9", "button", callback[4], callback[5], "no_call"]}],
                "delivered": [{post: ["delivery", "7", "delivered", callback[4], callback[5], "open"]}],
                "undelivered": [{post: ["delivery", "7", "undelivered", callback[4], callback[5], "open"]}]}
        return data[callback[3]]


class AdminButton:
    def __init__(self):
        self.on_shift_statuses = ["on_shift", "reserve_package", "packaging", "delivering"]
        self.employee = ['packer', 'courier']

    async def buttons_1(self, function: str, status: str) -> InlineKeyboardMarkup:
        if status in self.on_shift_statuses:
            buttons = [{"Заказы": ["order", "2", "0", "0", "0", "open"]},
                       {"Сотрудники": ["user", "2", "0", "0", "0", "open"]},
                       {"Информация": ["info", "1", "0", "0", "0", "open"]},
                       {"Завершить смену": ["main", "1", "0", "0", "0", "finish"]}]
        else:
            buttons = [{"Начать смену": ["main", "1", "0", "0", "0", "start"]},
                       {"Информация": ["info", "1", "0", "0", "0", "open"]},
                       {"Выйти": ["main", "0", "0", "0", "0", "close_bot"]}]
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_2_1(function: str) -> InlineKeyboardMarkup:
        buttons = [{"Управление 🔧": ['order', '3', 'manage', '0', '0', 'open']},
                   {"Сборка 📦": ['package', '2', '0', '0', '0', 'open'],
                    "Доставка 🛺": ['delivery', '2', '0', '0', '0', 'open']},
                   {"Назад": ['main', '1', '0', '0', '0', 'back']}]
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_3_1(function: str, orders: list, option: str) -> InlineKeyboardMarkup:
        buttons = [{order['posting_number']: ['order', '4', option, '0', order['posting_number'], 'open']}
                   for order in orders]
        buttons.append({'Назад': ['order', '2', '0', '0', '0', 'back']})
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_4_1(function: str, order: dict, callback: list) -> InlineKeyboardMarkup:
        option = FUNCTION['courier'] if order['start_delivery_date'] else (
            FUNCTION['packer'] if order['start_package_date'] else '0')
        buttons = [dict(Переназначить=['order', '4', option, '0', callback[5], 'reassign'])] if option != '0' else []
        if not order['cancel_reason_id']:
            buttons.append(dict(Отменить=['order', '5', '0', '0', callback[5], 'start_cancel']))
        buttons.append(dict(Назад=['order', '3', callback[3], '0', '0', 'back']))
        return await create_inline_keyboard(function, buttons)

    async def buttons_2_2(self, function: str) -> InlineKeyboardMarkup:
        buttons = [{FUNCTION[func].capitalize(): ['user', '3', func, '0', '0', 'open']} for func in self.employee]
        buttons.append(dict(Назад=['main', '1', '0', '0', '0', 'back']))
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_3_2(function: str, users_info: list, callback: list) -> InlineKeyboardMarkup:
        buttons = [{user['name']: ['user', '4', callback[3], '0', user['id'], 'open']} for user in users_info]
        buttons.append({'Назад': ['user', '2', '0', '0', '0', 'back'],
                        'Добавить': ['user', '4', callback[3], '0', '0', 'add']})
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_4_2(function: str, callback: list) -> InlineKeyboardMarkup:
        buttons = [{'Назад':   ['user', '3', callback[3], '0', '0', 'back'],
                    'Удалить': ['user', '3', callback[3], '0', callback[5], 'delete']}]
        return await create_inline_keyboard(function, buttons)


class CreatorButton:
    def __init__(self):
        self.employee = ['packer', 'courier', 'admin', 'moderator']

    @staticmethod
    async def buttons_1(function: str) -> InlineKeyboardMarkup:
        buttons = [{'Бот': ['bot', '2', '0', '0', '0', '0', 'open']},
                   {'Ozon Fresh': ['ozon', '2', '0', '0', '0', '0', 'open']}]
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_2_1(function: str) -> InlineKeyboardMarkup:
        buttons = [{'Перезагрузить': ['bot', '2', '0', '0', '0', '0', 'restart']},
                   {'Выключить': ['bot', '2', '0', '0', '0', '0', 'turn_off']},
                   {'API': ['bot', '3', '0', 'api', '0', '0', 'open']},
                   {'Назад': ['main', '1', '0', '0', '0', '0', 'back']}]
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_3_1(function: str, sellers: list) -> InlineKeyboardMarkup:
        buttons = [{seller['seller_name']: ['bot', '4', seller['seller_id'], 'api',
                                            seller['seller_name'], seller['status'], 'open']}
                   for seller in sellers]
        buttons.append({'Добавить': ['bot', '4', '0', 'api', '0', '0', 'add'],
                        'Назад': ['bot', '2', '0', '0', '0', '0', 'back']})
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_4_1(function: str, name: str, seller: str, status: str) -> InlineKeyboardMarkup:
        buttons = [{'Заменить API ключ': ['bot', '5', seller, 'api', name, '0', 'replace'],
                    'Деактивировать': ['bot', '3', seller, 'api', name, '0', 'delete']} if status == "active" else
                   {'Активировать': ['bot', '3', seller, 'api', name, '0', 'reactive']},
                   {'Назад': ['bot', '3', '0', 'api', '0', '0', 'back']}]
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_2_2(function: str, sellers: list) -> InlineKeyboardMarkup:
        buttons = [{seller['seller_name']: ['ozon', '3', seller['warehouse_id'], seller['seller_name'], '0', '0', 'open']}
                   for seller in sellers]
        buttons.append({'Назад': ['main', '1', '0', '0', '0', '0', 'back']})
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_3_2(function: str, seller: str) -> InlineKeyboardMarkup:
        buttons = [{'Сотрудники': ['ozon', '4', seller, 'user', '0', '0', 'open'],
                    'Заказы': ['ozon', '4', seller, 'order', '0', '0', 'pass']},
                   {'Назад': ['ozon', '2', '0', '0', '0', '0', 'back']}]
        return await create_inline_keyboard(function, buttons)

    async def buttons_4_2_1(self, function: str, seller: str, option: str) -> InlineKeyboardMarkup:
        buttons = [{FUNCTION[function].capitalize(): ['ozon', '5', seller, option, function, '0', 'open']}
                   for function in self.employee]
        buttons.append({'Назад': ['ozon', '3', seller, '0', '0', '0', 'back']})
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_5_2_1(function: str, users: list, seller: str, option: str, item: str) -> InlineKeyboardMarkup:
        buttons = [{user['name']: ['ozon', '6', seller, option, item, user['id'], 'open']} for user in users]
        buttons.append({'Добавить': ['ozon', '6', seller, option, item, '0', 'add'],
                        'Назад': ['ozon', '4', seller, option, '0', '0', 'back']})
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def buttons_6_2_1(function: str, seller: str, option: str, item: str, item_id: str) -> InlineKeyboardMarkup:
        buttons = [{'Удалить': ['ozon', '5', seller, option, item, item_id, 'delete'],
                    'Назад': ['ozon', '5', seller, option, item, '0', 'back']}] if item_id not in [
            '1', '7'] else [{'Назад': ['ozon', '5', seller, option, item, '0', 'back']}]
        return await create_inline_keyboard(function, buttons)


class BackButton:
    def __init__(self):
        self.functions = {"admin": self.user_admin_back_menu,
                          "moderator": "",
                          "creator": [self.user_create_back_menu_1, self.user_create_back_menu_2,
                                      self.user_create_back_menu_3]}

    @staticmethod
    async def user_create_back_menu_1(function: str) -> InlineKeyboardMarkup:
        buttons = [{'Назад': ['bot', '3', '0', 'api', '0', '0', 'back']}]
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def user_create_back_menu_2(function: str, seller: str, item: str) -> InlineKeyboardMarkup:
        buttons = [{'Назад': ['bot', '4', seller, 'api', '0', item, 'back']}]
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def user_create_back_menu_3(function: str, seller: str, item: str) -> InlineKeyboardMarkup:
        buttons = [{'Назад': ['ozon', '5', seller, "user", item, '0', 'back']}]
        return await create_inline_keyboard(function, buttons)

    @staticmethod
    async def user_admin_back_menu(function: str, option: str) -> InlineKeyboardMarkup:
        buttons = [{'Назад': ['user', '3', option, '0', '0', 'cancel']}]
        return await create_inline_keyboard(function, buttons)
    
