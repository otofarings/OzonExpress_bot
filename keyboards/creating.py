from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from data.condition import CALLBACK


# ****************************************InlineKeyboard****************************************
async def create_inline_keyboard(function: str, lst_of_rows: list) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()

    for row in lst_of_rows:
        buttons = []
        for text, args in row.items():
            buttons.append(InlineKeyboardButton(text=text, callback_data=(CALLBACK[function]).new(*args)))
        markup.row(*buttons)

    return markup


# ****************************************ReplyKeyboard****************************************
async def create_reply_keyboard(lst_of_rows: list, not_request_location: bool = False) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    if not_request_location:
        for row in lst_of_rows:
            buttons = []
            for key, args in row.items():
                buttons.append(KeyboardButton(args[0]))
            markup.row(*buttons)
    else:
        for row in lst_of_rows:
            buttons = []
            for args in row:
                buttons.append(KeyboardButton(args[0], request_location=False if len(args) <= 1 else args[1]))
            markup.row(*buttons)

    return markup


# ****************************************ReplyMarkupData****************************************
async def create_reply_markup(text: str, function: str, buttons: list) -> dict:
    return {"text": text, "reply_markup": await create_inline_keyboard(function, buttons)}


async def return_markup(markup: InlineKeyboardMarkup) -> dict:
    return {"reply_markup": markup}


if __name__ == "__main__":
    pass
