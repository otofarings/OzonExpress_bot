import aiogram.utils.markdown as fmt

from keyboards.creating import create_inline_keyboard


async def get_information(function: str) -> dict:
    text = [fmt.hbold("Информационное меню")]

    buttons = [{"Данные о боте": ["info", "2", "0", "0", "0", "info"]},
               {"Обучение":   ["info", "2", "0", "0", "0", "edu"]},
               {"Статистика": ["info", "2", "0", "0", "0", "stat"]},
               {"Назад":      ["main", "1", "0", "0", "0", "back"]}]

    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_info(function: str):
    text = [fmt.text("Информационное меню"),
            fmt.hbold("\nДанные о боте:")]
    buttons = [{'Назад': ['info', '1', '0', '0', '0', 'back']}]
    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_edu(function: str):
    url = "https://docs.google.com/presentation/d/1LzdEb1iFY501L8RQxHugcsXcT-lsgp7aTNitCDs3n4A/edit?usp=sharing"
    text = [fmt.text("Информационное меню"),
            fmt.hbold("\nОбучение:"),
            fmt.text("\n1.", fmt.hlink("Бизнес-процесс сборки и доставки", url))]
    buttons = [{'Назад': ['info', '1', '0', '0', '0', 'back']}]
    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}


async def get_stat(function: str):
    text = [fmt.text("Информационное меню"),
            fmt.hbold("\nСтатистика:")]
    buttons = [{'Назад': ['info', '1', '0', '0', '0', 'back']}]
    return {"text": fmt.text(*text, sep="\n"), "reply_markup": await create_inline_keyboard(function, buttons)}
