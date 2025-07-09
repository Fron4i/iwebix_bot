from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

__all__ = [
    "get_examples_keyboard",
    "get_case_keyboard",
]


def get_examples_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура списка демонстрационных проектов."""
    buttons = [
        [InlineKeyboardButton(text="🛒 Магазин-бот", callback_data="case_shop")],
        [InlineKeyboardButton(text="📆 Бронирование", callback_data="case_booking")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_case_keyboard(*, bot_url: str) -> InlineKeyboardMarkup:
    """Клавиатура карточки кейса с кнопкой запуска бота и возврата."""
    buttons = [
        [InlineKeyboardButton(text="🚀 Открыть бота", url=bot_url)],
        [InlineKeyboardButton(text="↩️ К списку", callback_data="examples")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons) 