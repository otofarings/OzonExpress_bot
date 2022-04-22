import collections

from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery

from states.fsm import PreviousMenu, get_fsm_data, save_fsm_data, finish_state
from utils.formate_text import PackerMenu
from utils.formate_button import PackerButton, create_reply_markup
from utils.message import send_info_log
from utils.db import sql
from utils.ozon_express_api.request import get_info, complete_packaging_ozon


packer_txt = PackerMenu()
packer_btn = PackerButton()


# ****************************************Packaging****************************************
async def get_level_1(function: str, status: str) -> dict:
    buttons = await packer_btn.pack_buttons_1(function, status)
    text = await packer_txt.pack_menu_1()
    return await create_reply_markup(text, buttons)


async def get_level_2(function: str, cll: CallbackQuery) -> dict:
    count = await sql.count_orders(cll.from_user.id, "awaiting_packaging")
    reserved_users = await sql.get_reserved_user(cll.from_user.id, "reserve_package")

    buttons = await packer_btn.pack_buttons_2(function, count)
    text = await packer_txt.pack_menu_2(count, reserved_users)
    return await create_reply_markup(text, buttons)


async def get_level_3(function: str, cll: CallbackQuery, state: FSMContext) -> dict:
    orders = await check_action_for_reserve_package(cll, state)

    buttons = await packer_btn.pack_buttons_3(function, orders)
    text = await packer_txt.pack_menu_3(orders)
    return await create_reply_markup(text, buttons)


async def get_level_4(function: str, cll: CallbackQuery, state: FSMContext) -> dict:
    order = (await get_fsm_data(state, ["data_"]))["data_"][int(cll.data.split(":")[3])]

    buttons = await packer_btn.pack_buttons_4(function, cll.data.split(":")[5])
    text = await packer_txt.pack_menu_4(order)
    return await create_reply_markup(text, buttons)


async def get_level_5(function: str, state: FSMContext, cll: CallbackQuery = None,
                      args: list = None, first: bool = False) -> dict:
    posting_number, obj, action = await get_callback_product_info(args if args else cll)

    if obj == "category":
        await save_fsm_data(state, product_rank=int(cll.data.split(":")[4]))
    products_info = await get_fsm_data(state, ["products", "product_rank", "all_ranks"])

    if first:
        data_lst = {}
        for product in products_info["products"]:
            if products_info["products"][product]['rank'] not in data_lst:
                category_name = await sql.get_product_category_name(products_info["products"][product]['rank'])
                data_lst[products_info["products"][product]['rank']] = category_name
        await save_fsm_data(state, category_names=data_lst)

    category_names = collections.OrderedDict(sorted(
        (await get_fsm_data(state, ["category_names"]))["category_names"].items()
    ))

    buttons = await packer_btn.pack_buttons_5(function, category_names, products_info, posting_number, obj, action)
    return {"reply_markup": buttons}


async def get_level_6(function: str, cll: CallbackQuery, state: FSMContext) -> dict:
    callback = cll.data.split(":")
    product = (await get_fsm_data(state, ["products"]))["products"][callback[3]]

    buttons = await packer_btn.pack_buttons_6(function, callback[5], callback[3])
    text = await packer_txt.pack_menu_6(product, callback[4])
    return await create_reply_markup(text, buttons)


async def get_level_7(function: str, cll: CallbackQuery) -> dict:
    callback = cll.data.split(":")
    products_info = await sql.get_products_info(callback[5])

    buttons = await packer_btn.pack_buttons_7(function, callback[5], callback[6])
    text = await packer_txt.pack_menu_7(products_info, callback[6])
    return await create_reply_markup(text, buttons)


async def get_level_8(function: str, tg_id: int, posting_number: str, tz: str, action: str) -> dict:
    products_info = await sql.get_products_info(posting_number)
    if action == "finish_cancel":
        status, cancel_status, posting_number = False, False, posting_number
    else:
        status, cancel_status, posting_number = await complete_packaging_ozon(products_info, tg_id)
    await finish_state(tg_id, tg_id)
    await check_cancellation_status(posting_number, tz, cancel_status, action)
    await send_info_log(tg_id, "Завершил сборку", posting_number, await check_completing_status(action, status))

    buttons = await packer_btn.pack_buttons_8(function)
    text = await packer_txt.pack_menu_8(posting_number, action)
    return await create_reply_markup(text, buttons)


# ****************************************Extra****************************************
async def check_action_for_reserve_package(cll: CallbackQuery, state):
    if cll.data.split(':')[6] == "reserve_package":
        await PreviousMenu.back_menu.set()
        orders_data = [dict(order) for order in await sql.reserve_orders_for_package(cll.from_user.id)]
        await save_fsm_data(state, data_=orders_data)
    else:
        orders_data = (await get_fsm_data(state, ["data_"]))["data_"]
    return orders_data


async def get_callback_product_info(new_data):
    lst, i1, i2, i3 = (new_data, 0, 1, 2) if type(new_data) is list else (new_data.data.split(":"), 5, 3, 6)
    return lst[i1], lst[i2], lst[i3]


async def check_change_in_quantity(quantity, fact_quantity) -> str:
    more = f"{quantity} -> " if quantity < fact_quantity else ""
    less = f" <- {quantity}" if quantity > fact_quantity else ""
    return f"{more}{fact_quantity}{less}"


async def update_product_quantity(product: dict, action: str, sku: int, posting_number) -> int:
    fact_quantity = product["fact_quantity"]
    if sku == product["sku"]:
        if (action == "minus") and (fact_quantity != 0):
            fact_quantity -= 1
        elif (action == "plus") and (fact_quantity < product["quantity"]):
            fact_quantity += 1
    await sql.update_product_fact_quantity(product["name"], fact_quantity, posting_number)
    return fact_quantity


async def get_product_weight(product) -> str:
    return product["weight"] if product["weight"] else "0"


async def format_product_name(index, product_name: str) -> str:
    lst_product_name = product_name.split(', ')
    return f"{index + 1}. {lst_product_name[-1]}, {', '.join(lst_product_name[:-1])}"


async def start_package(state: FSMContext, cll: CallbackQuery, tz: str) -> None:
    posting_number = cll.data.split(":")[5]
    dct_info = {}
    for product_info in await sql.get_products_info(posting_number):
        dct_info[str(product_info["sku"])] = {}
        for obj in dict(product_info):
            dct_info[str(product_info["sku"])][obj] = product_info[obj]
    await save_fsm_data(state, products=dct_info)
    await sql.start_package_order(cll.data.split(":")[5], cll.from_user.id, tz)
    await send_info_log(cll.from_user.id, "Начал сборку", cll.data.split(":")[5])
    return


async def check_cancellation_status(post_num: str, tz: str, cancel_status: bool = False, action: str = None) -> None:
    if cancel_status:
        await sql.cancel_order(post_num, tz)
    elif action != "finish_cancel":
        await sql.complete_package(post_num, tz)
    return


async def check_completing_status(action: str, status: str = None) -> str:
    return "Частично собран" if status else ("Отменен" if action == "finish_cancel" else "Полностью собран")


async def get_callback_data_for_back_button(function: str) -> list:
    return ["main", "1", "0", "0", "0", "back"] if function == 'packer' else ["order", "2", "0", "0", "0", "back"]


async def get_data_level_1(status: str) -> list:
    if status in ["on_shift", "reserve_package", "packaging"]:
        return [{"Сборка отправления": ["package", "2", "0", "0", "0", "open"]},
                {"Информация":         ["info", "1", "0", "0", "0", "open"]},
                {"Завершить смену":    ["main", "1", "0", "0", "0", "finish"]}]
    else:
        return [{"Начать смену": ["main", "1", "0", "0", "0", "start"]},
                {"Информация":   ["info", "1", "0", "0", "0", "open"]},
                {"Выйти":        ["main", "0", "0", "0", "0", "close_bot"]}]


async def get_data_level_2(count: int, callback_back: list) -> (str, list):
    if count != 0:
        buttons = [{"Назад":  callback_back,
                    "Сборка": ["package", "3", "0", "0", "0", "reserve_package"]}]
    else:
        buttons = [{"Назад":    callback_back,
                    "Обновить": ["package", "2", "0", "0", "0", "update"]}]
    return buttons


async def get_data_level_3(orders_data: list) -> (list, str):
    buttons = []
    for ind, order in enumerate(orders_data):
        buttons.append({f"Заказ №{ind + 1}": ["package", "4", ind, "0", order["posting_number"], "open"]})
    buttons.append({"Назад": ["package", "2", "0", "0", "0", "reserve_back"]})
    return buttons


async def get_info_for_products(cll: CallbackQuery) -> dict:
    products_info = {}
    for product in await sql.get_products_info(cll.data.split(":")[5]):
        products_info[str(product["sku"])] = {}
        info = await get_info(int(product["sku"]), cll.from_user.id)
        if info:
            for key, value in info.items():
                if key in ['id', 'name', 'barcode', 'category_id', 'price', 'volume_weight', 'primary_image']:
                    products_info[str(product["sku"])][key] = value
                    if key == 'category_id':
                        products_info[str(product["sku"])]['rank'] = await sql.get_product_rank(value)
                        products_info[str(product["sku"])]['sku'] = product["sku"]
    return products_info
