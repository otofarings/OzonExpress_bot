from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from loader import dp


class NewEmployee(StatesGroup):
    new_name = State()
    new_phone = State()
    new_warehouse_id = State()


class NewSeller(StatesGroup):
    town = State()
    seller_id = State()
    warehouse_id = State()
    api_key = State()
    timezone = State()
    log_chat_id = State()
    log_channel_id = State()


class NewAPIKey(StatesGroup):
    new_api_key = State()


class CancelReason(StatesGroup):
    reason = State()


class Geo(StatesGroup):
    geo = State()


class PreviousMenu(StatesGroup):
    back_menu = State()
    geo = State()
    cancel = State()
    special_cancel = State()
    weight = State()


async def finish_state(chat_id: int, user_id: int) -> None:
    state = dp.current_state(chat=chat_id, user=user_id)
    if state:
        await state.finish()
    return


async def check_state(state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    return


async def save_fsm_data(state: FSMContext, action: str = None, data_: list = None, status: str = None,
                        text: str = None, reply_markup=None, posting_number: str = None, menu: str = None,
                        sku: str = None, order_description: str = None, products: dict = None,
                        product_rank: int = None, category_names: dict = None) -> None:
    async with state.proxy() as data:
        if action:
            data['action'] = action
        if data_:
            data['data_'] = data_
        if status:
            data['status'] = status
        if posting_number:
            data['posting_number'] = posting_number
        if menu:
            data['menu'] = menu
        if order_description:
            data['order_description'] = order_description
        if products:
            data['products'] = products
            ranks = [products[product]['rank'] for product in products]
            data['product_rank'] = min(ranks)
            data['all_ranks'] = ranks
        if category_names:
            data['category_names'] = category_names
        if product_rank:
            if 'product_rank' in data:
                if data['product_rank'] == product_rank:
                    data['product_rank'] = None
                    return
            data['product_rank'] = product_rank
        if text:
            data['text'] = text
        if reply_markup:
            data['reply_markup'] = reply_markup
        if sku:
            data['sku'] = sku
    return


async def get_fsm_data(state: FSMContext, args: list) -> dict:
    fsm_data = {}
    async with state.proxy() as data:
        for arg in args:
            fsm_data[arg] = data[arg]
    return fsm_data


async def get_previous_menu(state: FSMContext) -> dict:
    fsm_data = {}
    async with state.proxy() as data:
        fsm_data['reply_markup'], fsm_data['text'] = data['reply_markup'], data['text']
    return fsm_data


if __name__ == '__main__':
    pass
