
USERS_STATE = {
    'unknown': 'неизвестный',
    'awaiting_activating': 'ожидает активации',
    'activated': 'активирован',
    'removed': 'удален',
}

FUNCTION = {
    'creator': 'создатель',
    'moderator': 'модератор',
    'admin': 'админ',
    'collector': 'сборщик',
    'courier': 'курьер',
}


EMPLOYEE_ACTION = {
    'started shift': 'начал смену',
    'finished shift': 'завершил смену',

    'started assembly': 'начал сборке',
    'canceled assembly': 'отменил сборку',
    'completed assembly': 'завершил сборку',

    'assignment order': 'назначение заказов',
    'assigned order': 'заказ назначен',
    'canceled assignment': 'отмена назначения',

    'picked order': 'забрал заказ со склада',
    'delivered order': 'доставил заказ',
    'undelivered order': 'не доставил заказ',
    'comes back': 'возвращается на склад',
    'returned order': 'вернул заказ на склад',
}

ORDER_STATUS = {
    'awaiting packaging': 'ожидает сборки',
    'started packaging': 'собирается',
    'finished packaging': 'собран',
    'canceled packaging': 'не собран',
    'partially packaging': 'частично собран',

    'awaiting deliver': 'ожидает отгрузки',
    'awaiting picking': 'ожидает отгрузки',
    'started delivering': 'доставляется',
    'finished delivering': 'условно доставлен',
    'seller_canceled delivering': 'отменен продавцом',
    'customer_canceled delivering': 'отменен покупателем',
    'returned back': 'возвращен на склад',
}

ORDER_STATE = {
    'awaiting_packaging': 'Ожидает сборки',
    'reserved_by_packer': 'Ожидает сборки',
    'packaging': 'Собирается',
    'awaiting_deliver': 'Ожидает отгрузки',
    'reserved_by_deliver': 'Ожидает отгрузки',
    'delivering': 'Доставляется',
    'cancelled': 'Отмененен',
    'delivered': 'Доставлен',
    'acceptance_in_progress': 'Идёт приёмка',
    'awaiting_approve': 'Ожидает подтверждения',
    'arbitration': 'Арбитраж',
    'client_arbitration': 'Клиентский арбитраж доставки',
    'not_accepted': 'Не принят на сортировочном центре',
    'conditionally_delivered': 'Условно доставлен'
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

}
