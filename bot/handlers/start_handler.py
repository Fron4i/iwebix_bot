from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from keyboards.navigation_menu_keyboard import get_navigation_menu
from database.user_repo import get_coupon

router = Router()

@router.message(CommandStart())
async def handle_start(message: types.Message, state: FSMContext) -> None:
    """Отправляет приветствие и главное меню."""
    await state.clear()
    greeting = (
        "Вас приветствует AI-помощник iWebix!\n\n\n"
        "Чем могу быть полезен?\n\n"
        "💡 расскажу, зачем нужен Telegram-бот\n\n"
        "💼 покажу работающие примеры\n\n"
        "💰 помогу рассчитать стоимость решения\n\n"
        "✉ свяжу вас напрямую с Ильей"
    )
    await message.answer(greeting)
    coupon_code = await get_coupon(message.from_user.id)
    await message.answer("Выберите нужный пункт меню:", reply_markup=get_navigation_menu(coupon_code)) 