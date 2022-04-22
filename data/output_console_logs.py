import logging

from .config import LOGGING_FORMAT


logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)


async def logging_info(*args):
    logging.info(*[str(arg) for arg in args])


async def logging_error(*args):
    logging.error(*[str(arg) for arg in args])
