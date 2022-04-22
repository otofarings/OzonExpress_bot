import aiogram.utils.markdown as fmt

from keyboards.creating import create_inline_keyboard


async def get_information(function: str) -> dict:
    text = [fmt.hbold("Информационное меню")]

    buttons = [{"Обновления": ["info", "2", "0", "0", "0", "info"]},
               {"Обучение":   ["info", "2", "0", "0", "0", "edu"]},
               {"Статистика": ["info", "2", "0", "0", "0", "stat"]},
               {"Назад":      ["main", "1", "0", "0", "0", "back"]}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_info(function: str):
    url_1 = "https://telegra.ph/MARSHRUTIZACIYA-I-KATEGORIZACIYA-TOVAROV-V-ZAKAZE-NA-SBORKU-03-30"
    url_2 = "https://telegra.ph/OTMENA-PRIVYAZKI-KURERU-OBYAZATELNOGO-ZAKAZA-NA-DOSTAVKU-03-30"
    url_3 = "https://telegra.ph/INFORMIROVANIE-O-REZERVIROVANII-ZAKAZA-04-11"
    url_4 = "https://telegra.ph/DOBAVLENIE-OTPRAVLENIYA-NA-DOSTAVKU-04-11"
    url_5 = "https://telegra.ph/UVEDOMLENIYA-O-ZAKAZAH-V-TELEGRAM-KANALE-04-12"
    text = [fmt.text("Информационное меню"),
            fmt.hbold("\nОбновления:\n\n"),
            fmt.text("=" * 30),
            fmt.hbold("\n12.04.2022:"),
            fmt.text("\n1.", fmt.hlink("Уведомления о заказах в телеграм-канале", url_5)),
            fmt.text("\n2.", fmt.hlink("Информирование о резервировании заказа", url_3)),
            fmt.text("\n3.", fmt.hlink("Добавление отправления на доставку", url_4)),
            fmt.text("=" * 30),
            fmt.hbold("\n30.03.2022:"),
            fmt.text("\n1.", fmt.hlink("Маршрутизация и категоризация товаров в заказе на сборку", url_1)),
            fmt.text("\n2.", fmt.hlink("Отмена привязки курьеру обязательного заказа на доставку", url_2)),
            fmt.text("=" * 30)]
    buttons = [{'Назад': ['info', '1', '0', '0', '0', 'back']}]
    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_edu(function: str):
    url_1 = "https://docs.google.com/presentation/d/1LzdEb1iFY501L8RQxHugcsXcT-lsgp7aTNitCDs3n4A/edit?usp=sharing"
    text = [fmt.text("Информационное меню"),
            fmt.hbold("\nОбучение:"),
            fmt.text("\n1.", fmt.hlink("Бизнес-процесс сборки и доставки", url_1))]
    buttons = [{'Назад': ['info', '1', '0', '0', '0', 'back']}]
    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_stat(function: str):
    text = [fmt.text("Информационное меню"),
            fmt.hbold("\nСтатистика:")]
    buttons = [{'Назад': ['info', '1', '0', '0', '0', 'back']}]
    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}
