from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

__all__ = ["get_navigation_menu"]

def get_navigation_menu() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру главного навигационного меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Зачем мне нужен бот", callback_data="need_bot")],
            [InlineKeyboardButton(text="📺 Примеры", callback_data="examples")],
            [InlineKeyboardButton(text="💰 Рассчитать стоимость", callback_data="calc_cost")],
            [InlineKeyboardButton(text="✉️ Написать мне", callback_data="contact_me")],
        ]
    ) 