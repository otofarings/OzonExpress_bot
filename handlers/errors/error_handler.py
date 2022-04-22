import functools
from contextlib import suppress

from aiogram.utils import exceptions as errors_1
from aiohttp import client_exceptions as errors_2

from loader import dp
from data.output_console_logs import logging_error


ERRORS = [errors_1.TelegramAPIError, errors_1.MessageNotModified, errors_1.CantParseEntities, errors_1.RetryAfter,
          errors_2.ContentTypeError, errors_2.ServerDisconnectedError, errors_2.ClientResponseError,
          errors_2.ClientConnectorError]


@dp.errors_handler()
async def errors_handler(update, exception):
    if isinstance(exception, errors_1.MessageNotModified):
        await logging_error('Message is not modified')
        return True
    if isinstance(exception, errors_1.CantParseEntities):
        await logging_error(f'CantParseEntities: {exception} \nUpdate: {update}')
        return True
    if isinstance(exception, errors_1.TelegramAPIError):
        await logging_error(f'TelegramAPIError: {exception} \nUpdate: {update}')
        return True
    if isinstance(exception, errors_1.RetryAfter):
        await logging_error(f'RetryAfter: {exception} \nUpdate: {update}')
        return True
    await logging_error(f'Update: {update} \n{exception}')


def skip_error():
    def wrapper(function_):
        @functools.wraps(function_)
        async def inner_function(*args, **kwargs):
            with suppress(*ERRORS):
                return await function_(*args, **kwargs)
        return inner_function
    return wrapper


def check_error():
    def wrapper(function_):
        @functools.wraps(function_)
        async def inner_function(*args, **kwargs):
            try:
                await function_(*args, **kwargs)
                return True
            except ERRORS as err:
                await logging_error(f"ERROR -  {err}")
                return False
        return inner_function
    return wrapper
