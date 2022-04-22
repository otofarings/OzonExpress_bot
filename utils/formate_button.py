from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData

from utils.db import sql


async def get_callback(function_: str, args: list) -> str:
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
        self.buttons = []
        self.fact_quantity = 0

    async def pack_buttons_1(self, function: str, status: str) -> InlineKeyboardMarkup:
        if status in ["on_shift", "reserve_package", "packaging"]:
            self.buttons = [{"Сборка отправления": ["package", "2", "0", "0", "0", "open"]},
                            {"Информация": ["info", "1", "0", "0", "0", "open"]},
                            {"Завершить смену": ["main", "1", "0", "0", "0", "finish"]}]
        else:
            self.buttons = [{"Начать смену": ["main", "1", "0", "0", "0", "start"]},
                            {"Информация": ["info", "1", "0", "0", "0", "open"]},
                            {"Выйти": ["main", "0", "0", "0", "0", "close_bot"]}]
        return await create_inline_keyboard(function, self.buttons)

    async def pack_buttons_2(self, function: str, count: int) -> InlineKeyboardMarkup:
        self.buttons = []
        back = ["main", "1", "0", "0", "0", "back"] if function == 'packer' else ["order", "2", "0", "0", "0", "back"]
        if count != 0:
            self.buttons.append({"Назад": back,
                                 "Сборка": ["package", "3", "0", "0", "0", "reserve_package"]})
        else:
            self.buttons.append({"Назад": back,
                                 "Обновить": ["package", "2", "0", "0", "0", "update"]})
        return await create_inline_keyboard(function, self.buttons)

    async def pack_buttons_3(self, function: str, orders: list) -> InlineKeyboardMarkup:
        self.buttons = []
        for ind, order in enumerate(orders):
            self.buttons.append({f"Заказ №{ind + 1}": ["package", "4", ind, "0", order["posting_number"], "open"]})
        self.buttons.append({"Назад": ["package", "2", "0", "0", "0", "reserve_back"]})
        return await create_inline_keyboard(function, self.buttons)

    async def pack_buttons_4(self, function: str, post_number_: str) -> InlineKeyboardMarkup:
        self.buttons = [{"Назад": ["package", "3", "0", "0", "0", "back"],
                         "Собрать": ["package", "5", "0", "0", post_number_, "start_packaging"]}]
        return await create_inline_keyboard(function, self.buttons)

    async def pack_buttons_5(self, function: str, category_names: dict, products_info: dict,
                             post: str, obj: str, action: str) -> InlineKeyboardMarkup:
        self.buttons = []
        for key, value in category_names.items():
            if key == products_info["product_rank"]:
                name = f"️🔽 ({products_info['all_ranks'].count(key)}) ️️{value}️"
                self.buttons.append({name: ["package", "5", "category", key, post, "open"]})

                count = 0
                for index, product in enumerate(await sql.get_products_info(post)):
                    if int(key) == int(products_info["products"][str(product["sku"])]["rank"]):
                        await self.write_fact_quantity(product, action, obj, post)
                        product_quantity = await self.check_change_in_quantity(product["quantity"])
                        product_name = await self.format_product_name(count, product['name'])
                        weight = await self.get_product_weight(product["weight"])

                        self.buttons.append({f"{product_name}": ["package", "6", product["sku"], weight, post, "open"]})
                        self.buttons.append({"-": ["package", "5", product["sku"], weight, post, "minus"],
                                             product_quantity: ["package", "4", product["sku"], weight, post, "pass"],
                                             "+": ["package", "5", product["sku"], weight, post, "plus"]})

                        await self.change_weight(weight, product["sku"], post)
                        count += 1
            else:
                name = f"⏹ ️({products_info['all_ranks'].count(key)}) {value}"
                self.buttons.append({name: ["package", "5", "category", key, post, "open"]})
        self.buttons.append({"Отменить": ["package", "9", "0", "0", post, "start_cancel"],
                             "Собран": ["package", "7", "0", "0", post, "open"]})
        return await create_inline_keyboard(function, self.buttons)

    async def pack_buttons_6(self, function: str, post_: str, sku_: str) -> InlineKeyboardMarkup:
        self.buttons = [{"Назад": ["package", "5", "0", "0", post_, "back"],
                         "Ввести вес": ["package", "9", sku_, "0", post_, "start_weight"]}]
        return await create_inline_keyboard(function, self.buttons)

    async def pack_buttons_7(self, function: str, post_: str, action: str) -> InlineKeyboardMarkup:
        list_action, action_name = await self.check_roll(action)
        self.buttons = [{action_name:   ["package", "7", "0", "0", post_, list_action]},
                        {"Назад":       ["package", "7", "0", "0", post_, "back"],
                         "Подтвердить": ["package", "8", "0", "0", post_, "confirm"]}]
        return await create_inline_keyboard(function, self.buttons)

    async def pack_buttons_8(self, function: str) -> InlineKeyboardMarkup:
        self.buttons = [{"Готово": ["package", "2", "0", "0", "0", "complete"]}]
        return await create_inline_keyboard(function, self.buttons)

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

    async def change_weight(self, weight: str, sku: int, post: str):
        if weight != "0":
            self.buttons[-1][f"{weight} гр"] = ["package", "9", sku, weight, post, "start_weight"]

    async def write_fact_quantity(self, product, action, obj, post):
        sku = int(product["sku"]) if obj == "category" else int(obj)
        await self.update_product_quantity(dict(product), action, sku, post)

    @staticmethod
    async def check_roll(action_: str):
        return ("roll_down", "Свернуть") if action_ == "roll_up" else ("roll_up", "Развернуть")


