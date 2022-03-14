from . import creator
from . import moderator
from . import admin
from . import packer
from . import courier


async def change_func(function: str):
    dct_of_functions = {
        "courier":   courier,
        "packer":    packer,
        "admin":     admin,
        "moderator": moderator,
        "creator":   creator
    }
    return dct_of_functions[function]
