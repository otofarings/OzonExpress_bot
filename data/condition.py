from aiogram.utils.callback_data import CallbackData

FUNCTION = {
    'courier':   'курьер',
    'packer':    'сборщик',
    'admin':     'админ',
    'moderator': 'модератор',
    'creator':   'создатель',
}

USERS_STATE = {
    'unknown':             'неизвестный',
    'awaiting_activating': 'ожидает активации',
    'activated':           'активирован',
    'removed':             'удален',
}

EMPLOYEE_STATUS = {
    'on_shift':      'на смене',
    'not_on_shift':  'не на смене',
    'providing_geo': 'предоставляет геоданные',

    'reserving':     'выбирает',
    'packaging':     'собирает',
    'delivering':    'доставляет',
    'returns':       'возвращается',
    'cancelling':    'отменяет'
}

ORDER_STATUS = {
    'awaiting_packaging':      'ожидает упаковки',
    'packaging':               'собирается',
    'canceled_packaging':      'не собран',
    'partially_packaging':     'частично собран',

    'awaiting_deliver':        'ожидает отгрузки',
    'delivering':              'доставляется',
    'conditionally_delivered': 'условно доставлен',
    'cancelled':               'отменен'
}

ORDER_STATUS_API = {
    'acceptance_in_progress': 'идёт приёмка',
    'awaiting_approve':       'ожидает подтверждения',
    'awaiting_packaging':     'ожидает упаковки',
    'not_accepted':           'не принят на сортировочном центре',
    'arbitration':            'арбитраж',
    'client_arbitration':     'клиентский арбитраж доставки',
    'awaiting_deliver':       'ожидает отгрузки',
    'delivering':             'доставляется',
    'delivered':              'доставлено',
    'cancelled':              'отменен'
}

CANCELLATION_STATUS = {
    352: 'Товар закончился на вашем складе',
    400: 'Сбой',
    402: 'Другая причина',
    358: 'Заказ отменен продавцом',
    359: 'Заказ не подготовлен продавцом',
    360: 'Заказ не отправлен',
    401: 'Отменен по спору',
    684: 'Покупатель не предоставил паспортные данные',
}

API_METHODS = {
    # Возвращает список складов.
    'v1': '/v1/warehouse/list',

    # Возвращает информацию о продукте
    'v2': '/v2/product/info',

    # Возвращает описание товара.
    'v3': '/v1/product/info/description',

    # Получения информации о количестве остатков для FBO.
    'v4': '/v2/product/info/stocks',

    # Возвращает список необработанных отправлений.
    'v5': '/v3/posting/fbs/unfulfilled/list',

    # Возвращает список отправлений за указанный период времени.
    'v6': '/v3/posting/fbs/list',

    # Делит заказ на отправления и переводит в статус «Ожидает доставки».
    # Каждый элемент items описывает отдельное отправление в заказе.
    # Разделить заказ нужно, если:
    # товары не помещаются в одну упаковку,
    # товары нельзя сложить в одну упаковку.
    'v7': '/v3/posting/fbs/ship',

    # Собирает заказ по одному из пакетов, на которые он был разбит.
    # Возвращает номера отправлений, которые получились после сборки.
    # Если в запросе передать часть продуктов из отправления,
    # то в результате обработки запроса первичное отправление разделится на две части.
    # В первичном несобранном отправлении останется часть продуктов, которую не передали в запросе.
    'v8': '/v3/posting/fbs/ship/package',

    # Перевести отправление в статус «Доставляется»'
    'v9': '/v2/fbs/posting/delivering',

    # Передает спорные заказы к отгрузке.
    # Статус отправления изменится на awaiting_deliver.
    'v10': '/v2/posting/fbs/awaiting-delivery',

    # Последняя миля
    'v11': '/v2/fbs/posting/last-mile',

    # Перевести отправление в статус «Доставлено»
    'v12': '/v2/fbs/posting/delivered',

    # Меняет статус отправления на cancelled.
    # Если значение параметра cancel_reason_id — 402, заполните поле cancel_reason_message.
    'v13': '/v2/posting/fbs/cancel',

    # Отменить отправку некоторых товаров в отправлении
    'v14': '/v2/posting/fbs/product/cancel',

    # Возвращет список причин отмены отправлений.
    'v15': '/v2/posting/fbs/cancel-reason/list',

    # Добавить вес для весовых товаров в отправлении
    'v16': '/v2/posting/fbs/product/change'

}

CALLBACK = {
    "courier": CallbackData("courier", "menu", "level", "option", "item", "item_id", "action"),
    "packer":  CallbackData("packer", "menu", "level", "option", "item", "item_id", "action"),
    "admin":   CallbackData("admin", "menu", "level", "option", "item", "item_id", "action")
}

ALERT_LOGS = {"1": "Отсутствует ответ на запрос списка отправлений за указанный период времени",
              "2": "В полученном ответе отсутствует результат запроса отправлений за указанный период времени",
              "3": "Возвращает пустой результат запроса отправлений за указанный период времени",
              "4": "Превышен лимит ожидания ответа от сервера. Повторная попытка через 15 секунд",
              "5": "Получены некорректные данные. Повторная попытка через 15 секунд",
              "6": "Потеря связи с сервером. Повторная попытка через 15 секунд",
              "7": "Ошибка соединения при получении ответа с сервера. Повторная попытка через 15 секунд",
              "8": "Не удается установить соединение с Proxy. Повторная попытка через 15 секунд",
              "9": "Завершение опроса API",
              "10": "Выход из процесса опроса API",
              "11": "Ошибка соединения",
              "12": "Ошибка - не подходящие данные",
              "13": "Ошибка - не подходящие данные при сравнении полученных значений с имеющимися",
              "14": "Не удалось добавить или изменить заказ"}

OZON_DELIVERY_METHOD_FIELDS = {"id":              {"type": int, "required": True},
                               "name":            {"type": str, "required": True},
                               "warehouse_id":    {"type": int, "required": True},
                               "warehouse":       {"type": str, "required": True},
                               "tpl_provider_id": {"type": int, "required": True},
                               "tpl_provider":    {"type": str, "required": True}}

OZON_CANCELLATION_FIELDS = {"cancel_reason_id":           {"type": int, "required": True},
                            "cancel_reason":              {"type": int, "required": True},
                            "cancellation_type":          {"type": int, "required": True},
                            "cancelled_after_ship":       {"type": int, "required": True},
                            "affect_cancellation_rating": {"type": int, "required": True},
                            "cancellation_initiator":     {"type": int, "required": True}}

OZON_CUSTOMER_ADDRESS_FIELDS = {"address_tail":      {"type": int, "required": True},
                                "city":              {"type": int, "required": True},
                                "comment":           {"type": int, "required": True},
                                "country":           {"type": int, "required": True},
                                "district":          {"type": int, "required": True},
                                "region":            {"type": int, "required": True},
                                "zip_code":          {"type": int, "required": True},
                                "latitude":          {"type": int, "required": True},
                                "longitude":         {"type": int, "required": True},
                                "pvz_code":          {"type": int, "required": True},
                                "provider_pvz_code": {"type": int, "required": True},
                                "name":              {"type": int, "required": True}}

OZON_CUSTOMER_FIELDS = {"customer_id":    {"type": int, "required": True},
                        "customer_email": {"type": int, "required": True},
                        "phone":          {"type": int, "required": True},
                        "address":        {"type": int, "required": True,
                                           "inner": OZON_CUSTOMER_ADDRESS_FIELDS, "inner_type": dict},
                        "name":           {"type": int, "required": True}}

OZON_PRODUCTS_FIELDS = {"price":          {"type": int, "required": True},
                        "offer_id":       {"type": int, "required": True},
                        "name":           {"type": int, "required": True},
                        "sku":            {"type": int, "required": True},
                        "quantity":       {"type": int, "required": True},
                        "mandatory_mark": {"type": int, "required": True}}

OZON_ADDRESSEE_FIELDS = {"name":  {"type": int, "required": True},
                         "phone": {"type": int, "required": True}}

OZON_REQUIREMENTS_FIELDS = {"products_requiring_gtd":     {"type": list, "required": True, "inner_type": str},
                            "products_requiring_country": {"type": list, "required": True, "inner_type": str}}

OZON_ANALYTICS_DATA_FIELDS = {"region":                  {"type": str, "required": True},
                              "city":                    {"type": str, "required": True},
                              "delivery_type":           {"type": str, "required": True},
                              "is_premium":              {"type": str, "required": True},
                              "payment_type_group_name": {"type": str, "required": True},
                              "warehouse_id":            {"type": str, "required": True},
                              "warehouse":               {"type": str, "required": True},
                              "tpl_provider_id":         {"type": str, "required": True},
                              "tpl_provider":            {"type": str, "required": True},
                              "delivery_date_begin":     {"type": str, "required": True},
                              "delivery_date_end":       {"type": str, "required": True},
                              "is_legal":                {"type": str, "required": True}}

OZON_PRODUCTS_ITEM_FIELDS = {"marketplace_service_item_fulfillment":                    {"type": str, "required": True},
                             "marketplace_service_item_pickup":                         {"type": str, "required": True},
                             "marketplace_service_item_dropoff_pvz":                    {"type": str, "required": True},
                             "marketplace_service_item_dropoff_sc":                     {"type": str, "required": True},
                             "marketplace_service_item_dropoff_ff":                     {"type": str, "required": True},
                             "marketplace_service_item_direct_flow_trans":              {"type": str, "required": True},
                             "marketplace_service_item_return_flow_trans":              {"type": str, "required": True},
                             "marketplace_service_item_deliv_to_customer":              {"type": str, "required": True},
                             "marketplace_service_item_return_not_deliv_to_customer":   {"type": str, "required": True},
                             "marketplace_service_item_return_part_goods_customer":     {"type": str, "required": True},
                             "marketplace_service_item_return_after_deliv_to_customer": {"type": str, "required": True}}

OZON_PRODUCTS_POST_FIELDS = {"marketplace_service_item_pickup":                         {"type": str, "required": True},
                             "marketplace_service_item_dropoff_pvz":                    {"type": str, "required": True},
                             "marketplace_service_item_dropoff_sc":                     {"type": str, "required": True},
                             "marketplace_service_item_dropoff_ff":                     {"type": str, "required": True},
                             "marketplace_service_item_direct_flow_trans":              {"type": str, "required": True},
                             "marketplace_service_item_return_flow_trans":              {"type": str, "required": True},
                             "marketplace_service_item_deliv_to_customer":              {"type": str, "required": True},
                             "marketplace_service_item_return_not_deliv_to_customer":   {"type": str, "required": True},
                             "marketplace_service_item_return_part_goods_customer":     {"type": str, "required": True},
                             "marketplace_service_item_return_after_deliv_to_customer": {"type": str, "required": True}}

OZON_FINANCIAL_DATA_PRODUCTS_FIELDS = {"commission_amount":      {"type": str, "required": True},
                                       "commission_percent":     {"type": str, "required": True},
                                       "payout":                 {"type": str, "required": True},
                                       "product_id":             {"type": str, "required": True},
                                       "old_price":              {"type": str, "required": True},
                                       "price":                  {"type": str, "required": True},
                                       "total_discount_value":   {"type": str, "required": True},
                                       "total_discount_percent": {"type": str, "required": True},
                                       "actions":                {"type": str, "required": True},
                                       "picking":                {"type": str, "required": True},
                                       "quantity":               {"type": str, "required": True},
                                       "client_price":           {"type": str, "required": True},
                                       "item_services":          {"type": str, "required": True}}

OZON_FINANCIAL_DATA_FIELDS = {"products":         {"type": str, "required": True},
                              "posting_services": {"type": str, "required": True}}

OZON_ORDER_FIELDS = {"posting_number":       {"type": str, "required": True},
                     "order_id":             {"type": int, "required": True},
                     "order_number":         {"type": str, "required": True},
                     "status":               {"type": str, "required": True},
                     "tracking_number":      {"type": str, "required": True},
                     "tpl_integration_type": {"type": str, "required": True},
                     "in_process_at":        {"type": str, "required": True},
                     "shipment_date":        {"type": str, "required": True},
                     "delivering_date":      {"type": str, "required": True},
                     "barcodes":             {"type": int, "required": True},
                     "analytics_data":       {"type": dict, "required": True},
                     "financial_data":       {"type": dict, "required": True},
                     "is_express":           {"type": bool, "required": True},
                     "delivery_method":      {"type": dict, "required": True,
                                              "inner": OZON_DELIVERY_METHOD_FIELDS},
                     "cancellation":         {"type": dict, "required": True,
                                              "inner": OZON_CANCELLATION_FIELDS},
                     "customer":             {"type": dict, "required": True,
                                              "inner": OZON_CUSTOMER_FIELDS},
                     "products":             {"type": list, "required": True,
                                              "inner": OZON_PRODUCTS_FIELDS},
                     "addressee":            {"type": dict, "required": True,
                                              "inner": OZON_ADDRESSEE_FIELDS},
                     "requirements":         {"type": dict, "required": True,
                                              "inner": OZON_REQUIREMENTS_FIELDS}}
