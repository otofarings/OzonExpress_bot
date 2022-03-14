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
