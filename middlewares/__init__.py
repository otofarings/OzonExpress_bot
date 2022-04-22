from loader import dp
from .throttling import ThrottlingMiddleware
from .protection import Protection, CallbackAntiFlood


if __name__ == "middlewares":
    dp.middleware.setup(CallbackAntiFlood())
    dp.middleware.setup(Protection())
