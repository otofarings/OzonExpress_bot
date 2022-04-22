import aiogram.utils.markdown as fmt

from keyboards.creating import create_reply_keyboard


async def create_keyboard_to_check_location():
    text = fmt.text("Для продолжения предоставьте местоположение, нажав кнопку ниже", fmt.hbold("Мое местоположение"))
    markup = await create_reply_keyboard([[["Назад"], ["Мое местоположение", True]]])
    return {'text': text, 'reply_markup': markup}


async def get_map_url(latitude, longitude):
    return f'https://yandex.ru/maps/?pt={longitude},{latitude}&z=17&l=map'
