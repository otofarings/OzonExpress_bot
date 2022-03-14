from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery
import aiogram.utils.markdown as fmt

from states.fsm import PreviousMenu, get_fsm_data, save_fsm_data, finish_state
from utils.geo import get_map_url
from utils.status import send_info_log
from utils.db import sql
from utils.ozon_express_api.request import get_info, complete_packaging_ozon
from keyboards.creating import create_inline_keyboard
from data.config import DEBUG


# ****************************************Packaging****************************************
async def get_level_1(function: str, status: str) -> dict:
    text = [fmt.hbold("Меню сборки 📦")]

    if status in ["on_shift", "reserve_package", "packaging"]:
        buttons = [{"Сборка отправления": ["package", "2", "0", "0", "0", "open"]},
                   {"Информация":         ["main", "1", "0", "0", "0", "pass"]},
                   {"Завершить смену":    ["main", "1", "0", "0", "0", "finish"]}]
    else:
        buttons = [{"Начать смену": ["main", "1", "0", "0", "0", "start"]},
                   {"Информация":   ["main", "1", "0", "0", "0", "pass"]},
                   {"Выйти":        ["main", "0", "0", "0", "0", "close_bot"]}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_2(function: str, cll: CallbackQuery) -> dict:
    text = [fmt.hbold("Меню сборки 📦\n")]

    count = await sql.count_orders(cll.from_user.id, "awaiting_packaging")
    text.append(fmt.text(fmt.hbold("Доступно:"), count))

    if function == 'packer':
        callback_back = ["main", "1", "0", "0", "0", "back"]
    else:
        callback_back = ["order", "2", "0", "0", "0", "back"]

    if count != 0:
        text.append(fmt.text("\nНажмите", fmt.hbold("Сборка"), ",чтобы перейти к выбору"))
        buttons = [{"Назад":  callback_back,
                    "Сборка": ["package", "3", "0", "0", "0", "reserve_package"]}]

    else:
        text.append(fmt.text("\nНажмите", fmt.hbold("Обновить"), "через несколько секунд"))
        buttons = [{"Назад":    callback_back,
                    "Обновить": ["package", "2", "0", "0", "0", "update"]}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_3(function: str, cll: CallbackQuery, state: FSMContext) -> dict:
    text = [fmt.hbold("Меню сборки 📦\n")]

    if cll.data.split(':')[6] == "reserve_package":
        await PreviousMenu.back_menu.set()
        orders_data = await sql.reserve_orders_for_package(cll.from_user.id)
        await save_fsm_data(state, data_=[dict(order) for order in orders_data])

    else:
        orders_data = (await get_fsm_data(state, ["data_"]))["data_"]

    text.append(fmt.text(fmt.hbold("\nДоступно:"), len(orders_data)))

    buttons = []
    for ind, order in enumerate(orders_data):
        text.append(fmt.text(fmt.hbold(f"\nЗаказ №{ind + 1}"),
                             fmt.text(fmt.hbold("Номер отправления:"), order["posting_number"]),
                             fmt.text(fmt.hbold("Товаров:"), order["sum"]),
                             fmt.text(fmt.hbold("Адрес:"),
                                      fmt.hlink(order["address"], await get_map_url(order["latitude"],
                                                                                    order["longitude"]))),
                             sep="\n"))
        buttons.append({f"Заказ №{ind + 1}": ["package", "4", ind, "0", order["posting_number"], "open"]})

    buttons.append({"Назад": ["package", "2", "0", "0", "0", "reserve_back"]})

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_4(function: str, cll: CallbackQuery, state: FSMContext) -> dict:
    text = [fmt.hbold("Меню сборки 📦\n")]

    callback = cll.data.split(":")

    order = (await get_fsm_data(state, ["data_"]))["data_"][int(callback[3])]

    text.append(fmt.text(fmt.text(fmt.hbold("Отправление:"), order["posting_number"]),
                         fmt.text("_" * 30),
                         fmt.text(fmt.hbold("Создан:"), order["in_process_at"]),
                         fmt.text(fmt.hbold("Передать курьеру до:"), order["shipment_date"]),
                         fmt.text("_" * 30),
                         fmt.text(fmt.hbold("Покупатель:"), fmt.hitalic(order["customer_name"])),
                         fmt.text(fmt.hbold("Тел. покупателя:"), fmt.hcode(f"+{order['customer_phone']}")),
                         fmt.text(fmt.hbold("Коментарий:"), order["customer_comment"]),
                         fmt.text("_" * 30),
                         fmt.text(fmt.hbold("Адрес:"), fmt.hlink(order["address"],
                                                                 await get_map_url(order["latitude"],
                                                                                   order["longitude"]))),
                         fmt.text("_" * 30),
                         fmt.text(fmt.hbold("Позиций:"), order["count"]),
                         fmt.text(fmt.hbold("Товаров:"), order["sum"]),
                         sep="\n"))

    buttons = [{"Назад":   ["package", "3", "0", "0", "0", "back"],
                "Собрать": ["package", "5", "0", "0", callback[5], "start_packaging"]}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_5(function: str, cll: CallbackQuery = None, args: list = None) -> dict:
    if args:
        posting_number = args[0]
        sku = args[1]
        action = args[2]
    else:
        callback = cll.data.split(":")
        posting_number = callback[5]
        sku = callback[3]
        action = callback[6]

    buttons = []
    for ind, order in enumerate(await sql.get_products_info(posting_number)):
        fact_quantity = order["fact_quantity"]

        if int(sku) == order["sku"]:
            if action == "minus":
                if fact_quantity != 0:
                    fact_quantity -= 1

            elif action == "plus":
                if fact_quantity < order["quantity"]:
                    fact_quantity += 1

            await sql.update_product_fact_quantity(order["name"], fact_quantity, posting_number)

        product_quantity = await check_change_in_quantity(order["quantity"], fact_quantity)
        product_name = await format_product_name(ind, order['name'])

        weight = order["weight"] if order["weight"] else "0"
        print(weight)

        buttons.append({product_name:         ["package", "6", order["sku"], weight, posting_number, "open"]})
        if weight != "0":
            buttons.append({"-":              ["package", "5", order["sku"], weight, posting_number, "minus"],
                            product_quantity: ["package", "4", order["sku"], weight, posting_number, "pass"],
                            "+":              ["package", "5", order["sku"], weight, posting_number, "plus"],
                            f"{weight} гр":   ["package", "9", order["sku"], weight, posting_number, "start_weight"]})
        else:
            buttons.append({"-":              ["package", "5", order["sku"], weight, posting_number, "minus"],
                            product_quantity: ["package", "4", order["sku"], weight, posting_number, "pass"],
                            "+":              ["package", "5", order["sku"], weight, posting_number, "plus"]})

    buttons.append({"Отменить":       ["package", "9", "0", "0", posting_number, "start_cancel"],
                    "Собран":         ["package", "7", "0", "0", posting_number, "open"]})

    return {"reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_6(function: str, cll: CallbackQuery) -> dict:
    text = [fmt.hbold("Меню сборки 📦\n")]

    callback = cll.data.split(":")

    if DEBUG:
        info = {"name": callback[2], "volume_weight": 5, "barcode": 8762436, "primary_image": "https://www.google.com"}
    else:
        info = await get_info(cll.from_user.id, int(callback[3]))

    text.append(fmt.text(info["name"],
                         fmt.text("=" * 30),
                         fmt.text(fmt.hbold("Объемный вес:"), info["volume_weight"]),
                         fmt.text(fmt.hbold("Штрих-код: "), info["barcode"]),
                         fmt.hide_link(info["primary_image"]),
                         sep="\n"))

    if callback[3] != "0":
        text.append(fmt.text(fmt.hbold("Введенный вес:"), callback[4]))

    buttons = [{"Назад":      ["package", "5", "0", "0", callback[5], "back"],
                "Ввести вес": ["package", "9", callback[3], "0", callback[5], "start_weight"]}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_7(function: str, cll: CallbackQuery) -> dict:
    text = [fmt.hbold("Меню сборки 📦\n")]

    callback = cll.data.split(":")

    order_info = await sql.get_products_info(callback[5])

    in_fact, should_be, in_fact_sku, should_be_sku = 0, 0, 0, 0
    for ind, order in enumerate(order_info):
        should_be += order["quantity"]
        should_be_sku += 1
        in_fact += order["fact_quantity"]
        in_fact_sku += 1 if order["fact_quantity"] != 0 else 0

    text_func = fmt.hcode if in_fact != should_be else fmt.text
    text_sku_func = fmt.hcode if in_fact_sku != should_be_sku else fmt.text

    text.append(fmt.text(fmt.text(f'Позиций:', text_sku_func(f'{in_fact_sku}'), f'из {should_be_sku}'),
                         fmt.text(f'Товаров: ', text_func(f'{in_fact}'), f'из {should_be}'),
                         sep='\n'))

    if callback[6] == "roll_up":
        for ind, order in enumerate(order_info):
            if ind == 0:
                text.append('=' * 30)
            else:
                text.append('_' * 30)

            text_func = fmt.hcode if order["quantity"] != order["fact_quantity"] else fmt.text

            text.append(fmt.text(f'{ind + 1}. {order["name"]}',
                                 fmt.text('Товаров:', text_func(order["fact_quantity"]), f'из {order["quantity"]}',
                                          fmt.hcode(f"({order['weight']} гр)") if order["weight"] else ""),
                                 sep='\n'))
        list_action, action_name = "roll_down", "Свернуть"

    else:
        list_action, action_name = "roll_up", "Развернуть"
        text.append(fmt.text("\nНажмите", fmt.hbold("Развернуть"), "для просмотра детальной информации"))

    buttons = [{action_name:   ["package", "7", "0", "0", callback[5], list_action]},
               {"Назад":       ["package", "7", "0", "0", callback[5], "back"],
                "Подтвердить": ["package", "8", "0", "0", callback[5], "confirm"]}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_level_8(function: str, tg_id: int, posting_number: str, tz: str, action: str) -> dict:
    text = [fmt.hbold("Меню сборки 📦\n")]

    products_info = await sql.get_products_info(posting_number)

    if action == "finish_cancel":
        status, cancel_status, posting_number = False, False, posting_number
        text.append(fmt.text(f"\nЗаказ успешно отменен", fmt.hbold(posting_number)))
    else:
        status, cancel_status, posting_number = await complete_packaging_ozon(products_info, tg_id)
        text.append(fmt.text(f"\nПоздравляем! Вы успешно завершили сборку заказа", fmt.hbold(posting_number)))

    buttons = [{"Готово": ["package", "2", "0", "0", "0", "complete"]}]

    await finish_state(tg_id, tg_id)

    if status:
        complete_status = "Частично"
    elif action == "finish_cancel":
        complete_status = "Отменен"
    else:
        complete_status = "Полностью"

    await send_info_log(tg_id, "Завершил сборку",
                        fmt.text(fmt.text(fmt.hbold("Заказ: "), fmt.hcode(posting_number)),
                                 fmt.text(fmt.hbold("Собран: "), complete_status),
                                 sep="\n"))

    if cancel_status:
        await sql.cancel_order(posting_number, tz)

    elif action != "finish_cancel":
        await sql.complete_package(posting_number, tz)

    else:
        pass

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


# ****************************************Extra****************************************
async def check_change_in_quantity(quantity, fact_quantity) -> str:
    more = f"{quantity} -> " if quantity < fact_quantity else ""
    less = f" <- {quantity}" if quantity > fact_quantity else ""
    return f"{more}{fact_quantity}{less}"


async def format_product_name(index, product_name: str) -> str:
    lst_product_name = product_name.split(', ')
    return f"{index + 1}. {lst_product_name[-1]}, {', '.join(lst_product_name[:-1])}"


async def start_package(cll: CallbackQuery, tz: str) -> None:
    posting_number = cll.data.split(":")[5]
    await sql.start_package_order(posting_number, cll.from_user.id, tz)
    await send_info_log(cll.from_user.id, "Начал сборку", fmt.text(fmt.hbold("Заказ:"), fmt.hcode(posting_number)))
    return
