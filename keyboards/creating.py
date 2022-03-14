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
async def create_reply_keyboard(lst_of_rows: list) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    for row in lst_of_rows:
        buttons = []
        for args in row:
            buttons.append(KeyboardButton(args[0], request_location=False if len(args) == 1 else args[1]))
        markup.row(*buttons)

    return markup


if __name__ == "__main__":
    pass
