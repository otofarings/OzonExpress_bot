from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import SkipHandler
from aiogram.types import CallbackQuery
from aiogram.utils.exceptions import MessageNotModified

from loader import dp
from data.condition import FUNCTION
from keyboards.inline import information


@dp.callback_query_handler(state='*')
async def open_info_menu(cll: CallbackQuery, function: str):
    callback = cll.data.split(":")
    if (function in FUNCTION) and (callback[1] == 'info'):
        try:
            if callback[2] == '1':
                await cll.message.edit_text(**await information.get_information(function))

            elif callback[2] == '2':
                if callback[6] == 'info':
                    await cll.message.edit_text(**await information.get_info(function), disable_web_page_preview=True)
                elif callback[6] == 'edu':
                    await cll.message.edit_text(**await information.get_edu(function), disable_web_page_preview=True)
                elif callback[6] == 'stat':
                    await cll.message.edit_text(**await information.get_stat(function), disable_web_page_preview=True)

        except MessageNotModified:
            return True
    else:
        raise SkipHandler

