import aiogram.utils.markdown as fmt

from data.condition import ORDER_STATUS_API, ORDER_STATUS, FUNCTION, USERS_STATE


b = fmt.hbold
t = fmt.text
c = fmt.hcode
h = fmt.hlink
i = fmt.hitalic
s = fmt.hstrikethrough
hl = fmt.hide_link

# ****************************************Constants****************************************
SYMBOL = {1: "\n", 2: "-", 3: "_", 4: "=", 5: "+", 6: ":", 7: "№", 8: "\xa0", 9: "@", 10: "#"}

EMOJI = {1: "📦", 2: "🛺", 3: "👔", 4: "🔧", 5: "👥", 6: "⚖️", 7: "❗"}

MENU = {1: b("Меню сборки" + EMOJI[1]),
        2: b("Меню доставки" + EMOJI[2]),
        3: b("Меню Администратора" + EMOJI[3]),
        4: b("Меню управления заказами" + EMOJI[4]),
        5: b("Меню управления сотрудниками" + EMOJI[5]),
        6: b("Меню ввода весовых данных" + EMOJI[6])}

BUTTON = {1: b("Сборка"),
          2: b("Доставка"),
          3: b("Обновить"),
          4: b("Развернуть"),
          5: b("Подтвердить"),
          6: b("Вернуться"),
          7: b("Возвращаюсь на склад")}

OBJ = {1:  b("Отправление" + SYMBOL[6]),
       2:  b("Отправления" + SYMBOL[6]),
       3:  b("Статус" + SYMBOL[6]),
       4:  b("Время создания" + SYMBOL[6]),
       5:  b("Передать курьеру до" + SYMBOL[6]),
       6:  b("Передать клиенту до" + SYMBOL[6]),
       7:  b("Позиций" + SYMBOL[6]),
       8:  b("Товаров" + SYMBOL[6]),
       9:  b("Отмена" + SYMBOL[6]),
       10: b("Причина отмены" + SYMBOL[6]),
       11: b("Инициатор отмены" + SYMBOL[6]),
       12: b("Получатель" + SYMBOL[6]),
       13: b("Тел. получателя" + SYMBOL[6]),
       14: b("Адрес" + SYMBOL[6]),
       15: b("Покупатель" + SYMBOL[6]),
       16: b("Тел. покупателя" + SYMBOL[6]),
       17: b("Коментарий" + SYMBOL[6]),
       18: b("Создан" + SYMBOL[6]),
       19: b("Заказ" + SYMBOL[6]),
       20: b("Объемный вес" + SYMBOL[6]),
       21: b("Введенный вес" + SYMBOL[6]),
       22: b("Штрих-код" + SYMBOL[6]),
       23: b("Собран" + SYMBOL[6]),
       24: b("Доступно" + SYMBOL[6]),
       25: b("Действие" + SYMBOL[6]),
       26: b("Время" + SYMBOL[6]),
       27: b("Заказ" + SYMBOL[8] + SYMBOL[7]),
       28: b("Прогресс" + SYMBOL[6]),
       29: b("Сборщик" + SYMBOL[6]),
       30: b("Начало сборки" + SYMBOL[6]),
       31: b("Завершение сборки" + SYMBOL[6]),
       32: b("Курьер" + SYMBOL[6]),
       33: b("Начало доставки" + SYMBOL[6]),
       34: b("Завершение доставки" + SYMBOL[6]),
       35: b("Количество {}ов" + SYMBOL[6]),
       36: b("Имя" + SYMBOL[6]),
       37: b("Телефон" + SYMBOL[6]),
       38: b("Никнейм" + SYMBOL[6]),
       39: b("Должность" + SYMBOL[6]),
       40: b("Дата регистрации" + SYMBOL[6]),
       41: b("Добавивший" + SYMBOL[6]),
       42: b("Время получения" + SYMBOL[6]),
       43: b("Причина" + SYMBOL[6]),
       44: b("С момента получения прошло" + SYMBOL[6])}

STAT = {1: "Завершил сборку",
        2: "Полностью",
        3: "Частично",
        4: "Отменен",
        5: EMOJI[7] + "Частичная отмена в заказе" + EMOJI[7],
        6: EMOJI[7] + "Полная отмена заказа" + EMOJI[7],
        7: "Новый заказ",
        8: "Отсутствует",
        9: "Завершен"}

TEXT = {1:  t(SYMBOL[1] + "Нажмите", BUTTON[3], "через несколько секунд"),
        2:  t(SYMBOL[1] + "Нажмите", BUTTON[2], "чтобы перейти к выбору"),
        3:  t(SYMBOL[1] + "Нажмите", BUTTON[1], "чтобы перейти к выбору"),
        4:  t("Отметив заказ(ы), нажмите", BUTTON[5], ", чтобы начать доставку"),
        5:  t(SYMBOL[1] + "Для выхода в главное меню, нажмите кнопку ниже"),
        6:  t("Необходимо забрать товары со склада"),
        7:  t("После передачи товара на склад, нажмите кнопку ниже, для выхода в главное меню"),
        8:  t("Нажмите", BUTTON[4], "для просмотра детальной информации"),
        9:  t("Введите в поле сообщения необходимый вес в" + fmt.hbold("ГРАММАХ")),
        10: t("ГРАММАХ"),
        11: t(EMOJI[7] + "Внимание" + EMOJI[7]),
        12: t("Наблюдаются технические проблемы с получением данных заказа"),
        13: t("Попробуйте изменить его статус в личном кабинете"),
        14: t(SYMBOL[1] + EMOJI[7] + "Статус 1го заказа был изменен, в связи с чем, он не доступен для доставки"),
        15: t(SYMBOL[1] + EMOJI[7] + "Статусы {} заказов были изменены, в связи с чем, они не доступны для доставки"),
        16: t("Выбрано 0 активных заказов"),
        17: t("Для продолжения нажмите", BUTTON[6]),
        18: t("Отлично! Вы доставили все заказы"),
        19: t("Вы завершили доставку" + SYMBOL[1] + "Не забудьте вернуть недоставленный товар на склад"),
        20: t("Нажмите кнопку", BUTTON[7], ", чтобы завершить доставку"),
        21: t("После передачи товара на склад, нажмите кнопку ниже, для выхода в главное меню"),
        22: t("Для выхода в главное меню, нажмите кнопку ниже"),
        23: t("Заказ {} успешно отменен"),
        24: t("Поздравляем! Вы успешно завершили сборку заказа "),
        25: t("Отметив заказ(ы), нажмите", BUTTON[5], ", чтобы добавить их к текущей доставке"),
        26: t("резервирует заказы"),
        27: t("резервируют заказы"),
        28: b("Заказы"),
        29: t(SYMBOL[1] + "Выберите должность" + SYMBOL[6]),
        30: t(SYMBOL[1] + "Список за последние 24 часа")}

LINKS = {1: "tg://user?id="}


# ****************************************Functions****************************************
async def symbol(ind_: int, quantity_: int) -> str:
    return SYMBOL[ind_] * quantity_


async def btn(ind_: int) -> str:
    return b(BUTTON[ind_])


async def user_function(function_: str) -> str:
    return b(FUNCTION[function_].capitalize() + SYMBOL[6])


async def comparison_values(in_fact_, should_be_):
    return c if in_fact_ != should_be_ else t


async def check_orders(in_fact: int, should_be: int) -> str:
    diff = should_be - in_fact
    return "" if diff <= 0 else (TEXT[14] if diff == 1 else TEXT[15].format(diff))


async def check_option(option_: str = None) -> str:
    return option_ if option_ else ""


async def check_options(args: list) -> list:
    options = []
    for index, arg in enumerate(args):
        if arg:
            if index == 0:
                options.append(t(OBJ[1], c(arg)))
            elif index == 1:
                options.append(t(OBJ[3], arg))
            elif index == 2:
                options.append(t(OBJ[43], arg))
    return options


async def check_cancel(status_: str, action_):
    return status_ if action_ != 'cancel' else 'cancelled'


async def phone(phone_: str) -> str:
    return c(SYMBOL[5] + phone_)


async def tg_link(tg_id_: int) -> str:
    return LINKS[1] + str(tg_id_)


async def nick_name(nick_name_) -> str:
    return t(SYMBOL[9] + nick_name_) if nick_name_ else STAT[8]


async def user_link(name_: str, tg_id_: int) -> str:
    return h(name_, await tg_link(tg_id_))


async def address(address_: str, latitude_: float, longitude_: float) -> str:
    from utils.geo import get_map_url
    return h(address_, await get_map_url(latitude_, longitude_))


async def hashtag(hashtags_):
    return t(" ".join([SYMBOL[10] + tag for tag in hashtags_]))


async def count_products(products: list) -> int:
    return sum([product["quantity"] for product in products])


async def unpack_posts(post_) -> (str, int):
    if isinstance(post_, str):
        return post_, 1
    elif isinstance(post_, list):
        return " ".join(post_), len(post_)
    else:
        return str(post_), 0


async def posting_name(post_) -> str:
    postings, count = await unpack_posts(post_)
    return b(OBJ[1 if count <= 1 else 2], c(postings))


async def postings_info_status(post_: str, status_: str) -> str:
    return t(await posting_name(post_), t(OBJ[23], status_), sep=SYMBOL[1])


async def edit_time(time) -> str:
    return str(time)[:-7] if time else STAT[8]


async def available(count: int) -> str:
    return t(OBJ[24], count)


async def complete_delivery(in_process_: int, undelivered_: int) -> str:
    return await txt([TEXT[18] if undelivered_ == 0 else TEXT[19], SYMBOL[1] + TEXT[20]]) if in_process_ == 0 else ""


async def txt(text_, sep_: int = None) -> str:
    text = text_ if isinstance(text_, list) else [text_]
    return t(*text, sep=await symbol(1, sep_ if sep_ else 1))


# ****************************************MarkupText****************************************
async def info_log(function: str, name: str, tg_id: int, time, action: str,
                   post_: str = None, status: str = None, reason: str = None) -> str:
    ex_option = await check_options([post_, status, reason])
    return await txt([*ex_option,
                      t(await user_function(function), await user_link(name, tg_id)),
                      t(OBJ[25], action),
                      t(OBJ[26], await edit_time(time))])


async def error_log(post_: str) -> str:
    return await txt([b(TEXT[11]),
                      t(TEXT[12], c(post_)),
                      t(TEXT[13])])


async def get_new_title(status_: str = None) -> str:
    return t(STAT[5] if status_ == "cancelled" else STAT[7]) if status_ else t(STAT[6])


async def order_description(order_, in_process_at_, shipment_date_, complete_time_,
                            hashtags: list, title_=None, status_=None) -> str:
    return await txt([i(title_) if title_ else "",
                      await txt([t(OBJ[1], order_["posting_number"]),
                                 t(OBJ[3], ORDER_STATUS[status_ if status_ else order_["status"]]),
                                 t(OBJ[4], str(in_process_at_)),
                                 t(OBJ[5], str(shipment_date_)),
                                 t(OBJ[6], str(complete_time_)),
                                 t(OBJ[7], len(order_["products"])),
                                 t(OBJ[8], await count_products(order_["products"])),
                                 s(SYMBOL[8] * 30),
                                 t(OBJ[12], i(order_["addressee"]["name"])),
                                 t(OBJ[13], await phone(order_['addressee']['phone'])),
                                 t(OBJ[14], order_["customer"]["address"]["address_tail"]),
                                 s(SYMBOL[8] * 30),
                                 t(OBJ[15], i(order_["customer"]["name"])),
                                 t(OBJ[16], await phone(order_['customer']['phone'])),
                                 t(OBJ[17], order_['customer']['address']['comment'])]),
                      (await hashtag(hashtags))], 2)


async def edit_description(title_, order_, complete_time_, hashtags_: list = None) -> str:
    return await txt([i(title_),
                      await txt([t(OBJ[1], order_["posting_number"]),
                                 t(OBJ[3], ORDER_STATUS[order_["status"]]),
                                 t(OBJ[4], order_["in_process_at"]),
                                 t(OBJ[5], order_["shipment_date"]),
                                 t(OBJ[6], str(complete_time_)),
                                 t(OBJ[7], order_["count"]),
                                 t(OBJ[8], order_["sum"]),
                                 s(SYMBOL[8] * 30),
                                 t(OBJ[12], i(order_["addressee_name"])),
                                 t(OBJ[13], await phone(order_['addressee_phone'])),
                                 t(OBJ[14], order_["address"]),
                                 s(SYMBOL[8] * 30),
                                 t(OBJ[15], i(order_["customer_name"])),
                                 t(OBJ[16], await phone(order_['customer_phone'])),
                                 t(OBJ[17], order_['customer_comment'])]),
                      (await hashtag(hashtags_)) if hashtags_ else ""], 2)


async def description_for_admin(order_, complete_time_, action_) -> str:
    return await txt([await txt([t(OBJ[1], order_["posting_number"]),
                                 t(OBJ[3], ORDER_STATUS[await check_cancel(order_["status"], action_)].capitalize()),
                                 t(OBJ[7], order_["count"]),
                                 t(OBJ[8], order_["sum"]),
                                 s(SYMBOL[8] * 30),
                                 t(OBJ[4], order_["in_process_at"]),
                                 t(OBJ[30], order_["start_package_date"]),
                                 t(OBJ[31], order_["finish_package_date"]),
                                 t(OBJ[29], await user_link('', order_['packer_id'])),
                                 s(SYMBOL[8] * 30),
                                 t(OBJ[5], order_["shipment_date"]),
                                 t(OBJ[33], order_["start_delivery_date"]),
                                 t(OBJ[6], str(complete_time_)),
                                 t(OBJ[34], order_["finish_delivery_date"]),
                                 t(OBJ[29], await user_link('', order_['deliver_id'])),
                                 s(SYMBOL[8] * 30),
                                 t(OBJ[9], order_["cancel_reason_id"]),
                                 t(OBJ[10], order_["cancel_reason"]),
                                 t(OBJ[11], order_["cancellation_initiator"]),
                                 s(SYMBOL[8] * 30),
                                 t(OBJ[12], i(order_["addressee_name"])),
                                 t(OBJ[13], await phone(order_['addressee_phone'])),
                                 t(OBJ[14], order_["address"]),
                                 s(SYMBOL[8] * 30),
                                 t(OBJ[15], i(order_["customer_name"])),
                                 t(OBJ[16], await phone(order_['customer_phone'])),
                                 t(OBJ[17], order_['customer_comment'])])])


async def cancel_description(order_: dict, title_: str) -> str:
    return await txt([await txt([i(title_),
                                 t(OBJ[1], order_["posting_number"]),
                                 t(OBJ[3], ORDER_STATUS[order_["status"]].capitalize()),
                                 t(OBJ[7], len(order_["products"])),
                                 t(OBJ[8], await count_products(order_["products"])),
                                 s(SYMBOL[8] * 30),
                                 t(OBJ[9], order_["cancellation"]["cancel_reason_id"]),
                                 t(OBJ[10], order_["cancellation"]["cancel_reason"]),
                                 t(OBJ[11], order_["cancellation"]["cancellation_initiator"]),
                                 s(SYMBOL[8] * 30)])])


async def description_for_packer(order_) -> str:
    return await txt([t(OBJ[1], order_["posting_number"]),
                      s(SYMBOL[8] * 30),
                      t(OBJ[4], order_["in_process_at"]),
                      t(OBJ[5], order_["shipment_date"]),
                      s(SYMBOL[8] * 30),
                      t(OBJ[15], i(order_["customer_name"])),
                      t(OBJ[16], await phone(order_['customer_phone'])),
                      t(OBJ[17], order_["customer_comment"]),
                      s(SYMBOL[8] * 30),
                      t(OBJ[14], await address(order_["address"], order_["latitude"], order_["longitude"])),
                      s(SYMBOL[8] * 30),
                      t(OBJ[7], order_["count"]),
                      t(OBJ[8], order_["sum"])])


async def description_for_deliver(order_: dict):
    return await txt([t(OBJ[1], order_["posting_number"]),
                      t(OBJ[6], str(order_["shipment_date"])),  # Проверить время
                      s(SYMBOL[8] * 30),
                      t(OBJ[14], await address(order_["address"], order_["latitude"], order_["longitude"])),
                      s(SYMBOL[8] * 30),
                      t(OBJ[12], i(order_['addressee_name'])),
                      t(OBJ[16], await phone(order_['addressee_phone'])),
                      s(SYMBOL[8] * 30),
                      t(OBJ[17], order_['customer_comment'])])


async def description_1(ind, order_) -> str:
    return await txt([s(SYMBOL[8] * 30),
                      t(OBJ[27] + b(ind + 1)),
                      t(OBJ[1], order_["posting_number"]),
                      t(OBJ[8], order_["sum"]),
                      t(OBJ[14], await address(order_["address"], order_["latitude"], order_["longitude"]))])


async def description_2(order_, complete_time_) -> str:
    return await txt([t(SYMBOL[1] + OBJ[1], order_["posting_number"]),
                      t(OBJ[6], str(complete_time_)),
                      s(SYMBOL[8] * 30),
                      t(OBJ[14], await address(order_["address"], order_["latitude"], order_["longitude"]))])


async def product_detail_info(info) -> str:
    return await txt([t(SYMBOL[1] + info['name']),
                      s(SYMBOL[8] * 30),
                      t(OBJ[20], info["volume_weight"]),
                      t(OBJ[22], info["barcode"]),
                      hl(info["primary_image"])])


async def employee_description(user_: dict) -> str:
    return await txt([t(OBJ[36], user_["name"]),
                      t(OBJ[37], await phone(user_["phone"])),
                      t(OBJ[38], await nick_name(user_["username"])),
                      t(OBJ[39], FUNCTION[user_["function"]]),
                      t(OBJ[3], USERS_STATE[user_["state"]]),
                      t(OBJ[40], await edit_time(user_["begin_date"])),
                      t(OBJ[41], await nick_name(user_["added_by_name"]))])


async def inputted_weight(weight: str) -> str:
    return t(OBJ[21], weight)


async def get_current_quantity(products_: list) -> (int, int, int, int):
    in_fact, should_be, in_fact_sku, should_be_sku = 0, 0, 0, 0
    for order in products_:
        should_be += order["quantity"]
        should_be_sku += 1
        in_fact += order["fact_quantity"]
        in_fact_sku += 1 if order["fact_quantity"] != 0 else 0
    return in_fact, should_be, in_fact_sku, should_be_sku


async def products_quantity(products_) -> str:
    in_fact, should_be, in_fact_sku, should_be_sku = await get_current_quantity(products_)
    text_sku_func = await comparison_values(in_fact_sku, should_be_sku)
    text_func = await comparison_values(in_fact, should_be)
    return await txt([t(OBJ[7], text_sku_func(in_fact_sku), "из", should_be_sku),
                      t(OBJ[8], text_func(in_fact), "из", should_be)])


async def products_quantity_detail(ind_: int, product_) -> str:
    text_func = await comparison_values(product_["fact_quantity"], product_["quantity"])
    return await txt([t(SYMBOL[4] if ind_ == 0 else s(SYMBOL[8])) * 30,
                      t(f'{ind_ + 1}. {product_["name"]}'),
                      t(OBJ[8], text_func(product_["fact_quantity"]), "из", product_["quantity"]),
                      c(f"({product_['weight']} гр)") if product_["weight"] else ""], 0)


async def order_detail_info(products_: list) -> str:
    return await txt([await products_quantity_detail(product[0], product[1]) for product in list(enumerate(products_))],
                     0)


async def reserving_users(users_: list):
    if len(users_) < 1:
        return ""
    elif len(users_) == 1:
        return c(users_[0]["name"], TEXT[26])
    else:
        return c(", ".join([user["name"] for user in users_]), TEXT[27])


class DeliverMenu:
    def __init__(self):
        self.menu = MENU[2]

    async def menu_1(self) -> str:
        return self.menu

    async def menu_2(self, count_: int, users_: list) -> str:
        return await txt([self.menu,
                          await available(count_),
                          SYMBOL[1],
                          await reserving_users(users_),
                          TEXT[2] if count_ > 0 else TEXT[1]])

    async def menu_3(self, count_: int, action_: str) -> str:
        return await txt([self.menu,
                          await available(count_),
                          SYMBOL[1],
                          TEXT[25] if action_ == "ex_add" else TEXT[4]])

    async def menu_4(self, order_, complete_time_) -> str:
        return await txt([self.menu,
                          await description_2(order_, complete_time_)])

    async def menu_6(self, orders_in_fact_: int, orders_should_be_: int) -> str:
        if orders_in_fact_ > 0:
            return await txt([self.menu,
                              SYMBOL[1],
                              TEXT[6],
                              await check_orders(orders_in_fact_, orders_should_be_)])
        else:
            return await txt([self.menu,
                              TEXT[16],
                              TEXT[17]], 2)

    async def menu_7(self, order_: dict) -> str:
        return await txt([self.menu,
                          await description_for_deliver(order_)], 2)

    async def menu_8(self, count_: int) -> str:
        return await txt([self.menu,
                          t(OBJ[28], b(str(0)), "из", b(count_))], 2)

    async def menu_9(self, in_process_: int, delivered_: int, undelivered_: int) -> str:
        total_count = in_process_ + delivered_ + undelivered_
        return await txt([self.menu,
                          t(OBJ[28], b(str(total_count - in_process_)), "из", total_count),
                          await complete_delivery(in_process_, undelivered_)], 2)

    async def menu_10(self, consist_: str) -> str:
        return await txt([self.menu,
                          TEXT[21] if consist_ == "undelivered" else TEXT[22]], 2)

    async def menu_11(self, count_: int) -> str:
        return await txt([self.menu,
                          await available(count_),
                          SYMBOL[1],
                          TEXT[25]])


class PackerMenu:
    def __init__(self):
        self.menu = MENU[1]

    async def pack_menu_1(self) -> str:
        return self.menu

    async def pack_menu_2(self, count_: int, users_: list) -> str:
        return await txt([self.menu,
                          await available(count_),
                          SYMBOL[1],
                          await reserving_users(users_),
                          TEXT[3] if count_ > 0 else TEXT[1]])

    async def pack_menu_3(self, orders_: list) -> str:
        return await txt([self.menu,
                          await txt([await description_1(order[0], order[1]) for order in list(enumerate(orders_))])])

    async def pack_menu_4(self, order_: dict) -> str:
        return await txt([self.menu,
                          await description_for_packer(order_)], 2)

    async def pack_menu_6(self, product_, weight_):
        return await txt([self.menu,
                          await product_detail_info(product_),
                          await inputted_weight(weight_) if weight_ != "0" else ""])

    async def pack_menu_7(self, products_: list, action: str) -> str:
        return await txt([self.menu,
                          await products_quantity(products_),
                          await order_detail_info(products_) if action == "roll_up" else TEXT[8]], 2)

    async def pack_menu_8(self, post_num_: str, action_: str) -> str:
        return await txt([self.menu,
                          TEXT[23].format(post_num_) if action_ == "finish_cancel" else TEXT[24] + post_num_], 2)

    @staticmethod
    async def edit_order_msg(title_: str, order_: dict, complete_time) -> str:
        return await edit_description(title_, order_, complete_time)


class AdminMenu:
    def __init__(self):
        self.menu_admin = MENU[3]
        self.menu_orders = MENU[4]
        self.menu_employee = MENU[5]

    async def admin_menu_1(self) -> str:
        return self.menu_admin

    async def orders_menu_2(self) -> str:
        return await txt([self.menu_admin,
                          TEXT[28]])

    async def orders_menu_3(self, count_: int) -> str:
        return await txt([self.menu_orders,
                          await available(count_),
                          TEXT[30]])

    async def orders_menu_4(self, order_: dict, complete_time_, action_: str) -> str:
        return await txt([self.menu_orders,
                          await description_for_admin(order_, complete_time_, action_)])

    async def orders_menu_5(self) -> str:
        return self.menu_orders

    async def employee_menu_2(self) -> str:
        return await txt([self.menu_employee,
                          TEXT[29]])

    async def employee_menu_3(self, function: str) -> str:
        return await txt([self.menu_employee,
                          OBJ[35].format(FUNCTION[function])])

    async def employee_menu_4(self, user_: dict) -> str:
        return await txt([self.menu_employee,
                          await employee_description(user_)])


async def weighting_product(name: str, not_digit: bool) -> list:
    text = [fmt.text("Меню ввода весовых данных\n"), fmt.hbold(name)]
    if not_digit:
        text.append(fmt.text("\n❗Неверный формат! Попробуйте снова"))
    else:
        text.append(fmt.text("\nВведите в поле сообщения необходимый вес в", fmt.hbold("ГРАММАХ")))
    text.append(fmt.text("\nПример: 420 или 1280"))
    return text


if __name__ == '__main__':
    pass
