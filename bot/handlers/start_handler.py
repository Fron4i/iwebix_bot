from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from keyboards.navigation_menu_keyboard import get_navigation_menu

router = Router()

@router.message(CommandStart())
async def handle_start(message: types.Message, state: FSMContext) -> None:
    """Отправляет приветствие и главное меню."""
    await state.clear()
    greeting = (
        "Здравствуйте! Вас приветствует виртуальный помощник Ильи Фомича. "
        "Я расскажу, зачем нужен Telegram-бот, покажу работающие примеры, помогу "
        "рассчитать стоимость решения и свяжу вас напрямую с автором."
    )
    await message.answer(greeting)
    await message.answer("Выберите нужный пункт меню:", reply_markup=get_navigation_menu()) 