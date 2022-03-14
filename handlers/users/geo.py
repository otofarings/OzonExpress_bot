from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import SkipHandler
from aiogram.types import Message, CallbackQuery
from aiogram.utils.exceptions import MessageNotModified

from loader import dp
from data.condition import FUNCTION
from states.fsm import PreviousMenu, get_fsm_data, save_fsm_data
from utils.message import del_old_msg, del_msg, update_msg
from utils.geo import create_keyboard_to_check_location
from utils.status import change_status
from keyboards.inline import change_func


@dp.message_handler(content_types=['location'], state=[PreviousMenu.geo])
async def get_geo(msg: Message, function: str, status, state: FSMContext, tz: str):
    if function in FUNCTION:
        if status in ["on_shift", "not_on_shift"]:
            fsm_data = await get_fsm_data(state, ['action', 'status'])
            status = await change_status(function, fsm_data['action'], fsm_data['status'],
                                         msg.from_user.id, tz, dict(msg.location))
            func = await change_func(function)
            new_msg = await msg.answer(**await func.get_level_1(function, status))
            await state.finish()

        elif status in ['delivering']:
            fsm_data = await get_fsm_data(state, ['reply_markup', 'action'])
            func = await change_func("courier")
            new_msg = await msg.answer(**await func.get_level_9(function, tz, reply_markup=fsm_data['reply_markup'],
                                                                callback=fsm_data['action'], tg_id=msg.from_user.id,
                                                                location=msg.location))
            await PreviousMenu.back_menu.set()

        else:
            raise SkipHandler

        await update_msg(new_msg)
        await del_msg(msg)

    else:
        raise SkipHandler


@dp.message_handler(state=[PreviousMenu.geo])
async def get_geo_back(msg: Message, function: str, status, state: FSMContext):
    if function in FUNCTION:
        if msg.text == 'Назад':
            if status in ["on_shift", "not_on_shift"]:
                fsm_data = await get_fsm_data(state, ['status'])
                func = await change_func(function)
                new_msg = await msg.answer(**await func.get_level_1(function, fsm_data['status']))
                await state.finish()

            elif status in ['delivering', 'packaging']:
                fsm_data = await get_fsm_data(state, ['reply_markup', 'text'])
                new_msg = await msg.answer(text=fsm_data['text'], reply_markup=fsm_data['reply_markup'])
                await PreviousMenu.back_menu.set()

            else:
                raise SkipHandler

            await update_msg(new_msg)
            await del_msg(msg)

    else:
        raise SkipHandler


@dp.callback_query_handler(state='*')
async def open_main_menu(cll: CallbackQuery, function: str, tz: str, status, state: FSMContext):
    callback = cll.data.split(":")
    if (function in FUNCTION) and (callback[1] == 'main'):
        try:
            await state.finish()
            if (callback[6] in ['start', 'finish']) and (status in ["on_shift", "not_on_shift"]):
                await PreviousMenu.geo.set()
                await save_fsm_data(state, action=callback[6], status=status)
                new_msg = await cll.message.answer(**await create_keyboard_to_check_location())

                await update_msg(new_msg)
                await del_msg(cll.message)

            else:
                status = await change_status(function, callback[6], status, cll.from_user.id, tz)

                if callback[6] == 'close_bot':
                    await del_old_msg(cll.from_user.id, cll.message.message_id)

                else:
                    func = await change_func(function)
                    await cll.message.edit_text(**await func.get_level_1(function, status))

        except MessageNotModified:
            return True

    else:
        raise SkipHandler
