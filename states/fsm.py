from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from loader import dp


async def finish_state(chat_id: int, user_id: int):
    state = dp.current_state(chat=chat_id, user=user_id)
    if state:
        await state.finish()
    return


async def check_state(state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    return


class NewEmployee(StatesGroup):
    new_name = State()
    new_phone = State()
    new_warehouse_id = State()


class NewSeller(StatesGroup):
    town = State()
    seller_id = State()
    api_key = State()
    timezone = State()
    log_chat_id = State()


class NewAPIKey(StatesGroup):
    new_api_key = State()


class CancelReason(StatesGroup):
    reason = State()


class DeliveringOrder(StatesGroup):
    get_orders = State()
    delivery = State()
    back = State()


class Geo(StatesGroup):
    geo = State()


class PreviousMenu(StatesGroup):
    back_menu = State()
    geo = State()


if __name__ == '__main__':
    pass
