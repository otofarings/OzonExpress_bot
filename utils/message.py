from contextlib import suppress

from aiogram.types import Message
import aiogram.utils.markdown as fmt
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound, MessageNotModified

from loader import dp
from data.config import MODER_LOGS
from utils.db import sql
from utils.proccess_time import get_time
from utils.status import change_status


async def send_message_to_logs(start_up: bool = False, turn_off: bool = False, txt=''):
    for recipient in [MODER_LOGS]:
        if start_up:
            txt = f"Бот Запущен!"
            await sql.write_bot_start_status()

        elif turn_off:
            txt = f"Бот Остановлен!"
            await sql.write_bot_finish_status()

        await send_msg(recipient, f'{await get_time()}: {txt}')
    return


async def send_msg(recipient, text):
    await dp.bot.send_message(chat_id=recipient, text=text)


async def cancel_action_message(posting_number):
    order_info = await sql.get_order_info_for_cancelling(posting_number)
    employee_info = {}

    if order_info["finish_delivery_date"] is None:
        if order_info["start_delivery_date"] is not None:
            pass
            # employee_info = await sql.get_employee_info_to_edit_msg(order_info["deliver_id"])

        elif order_info["finish_package_date"] is None:
            if order_info["start_package_date"] is not None:
                employee_info = await sql.get_employee_info_to_edit_msg(order_info["packer_id"])

    if employee_info:
        await edit_msg(employee_info, order_info)

    return


async def edit_msg(employee_info, order_info):
    from keyboards.creating import create_inline_keyboard

    text = fmt.text(fmt.text("                    ❗Заказ отменён❗\n"),
                    fmt.text(fmt.hbold("Номер отправления:"), order_info["posting_number"]),
                    fmt.text(fmt.hbold("Адрес:"), order_info["address"]),
                    fmt.text("\nДля возврата в главное меню, нажмите", fmt.hbold("Назад")),
                    sep="\n")
    buttons = [{'Назад': ['main', '1', '0', '0', '0', 'reserve_back']}]

    try:
        await dp.bot.edit_message_text(text=text,
                                       reply_markup=await create_inline_keyboard(employee_info["function"], buttons),
                                       chat_id=employee_info["tg_id"],
                                       message_id=employee_info["msg_id"])

        await change_status(employee_info["function"], "on_shift", employee_info["status"],
                            employee_info["tg_id"], employee_info["timezone"])

    except MessageNotModified:
        return True


async def update_msg(new_msg: Message) -> None:
    if new_msg:
        old_msg_id = await sql.update_msg(new_msg.message_id, new_msg.chat.id)

        if old_msg_id:
            await del_old_msg(new_msg.chat.id, old_msg_id)
    return


async def del_msg(msg: Message):
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await msg.delete()

    return


async def del_old_msg(chat_id, old_msg_id):
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await dp.bot.delete_message(chat_id, old_msg_id)
    return


async def push_info_msg(cll, text):
    await dp.bot.answer_callback_query(cll.id, text=text, show_alert=True)


if __name__ == "__main__":
    pass
