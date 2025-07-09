from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import quote
from typing import Optional
from config import settings

__all__ = ["get_navigation_menu"]


def _contact_button(coupon_code: Optional[str] = None) -> InlineKeyboardButton:
    base_text = "Приветствую!\n\nХочу обсудить создание Telegram-бота"
    if coupon_code:
        base_text += f"\nКупон: {coupon_code}"
    url = f"https://t.me/{settings.owner_username}?text=" + quote(base_text)
    return InlineKeyboardButton(text="✉ Написать мне", url=url)


def get_navigation_menu(coupon_code: Optional[str] = None) -> InlineKeyboardMarkup:
    """Клавиатура главного меню с учётом купона (если есть)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💡 Зачем мне нужен бот?", callback_data="need_bot")],
            [InlineKeyboardButton(text="💼 Примеры", callback_data="examples")],
            [InlineKeyboardButton(text="💰 Рассчитать стоимость", callback_data="calc_cost")],
            [_contact_button(coupon_code)],
        ]
    ) 