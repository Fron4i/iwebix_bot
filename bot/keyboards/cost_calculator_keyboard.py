from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional
from urllib.parse import quote

from services.cost_calculator_service import COST_TEMPLATES, MODULES, SUPPORT_PACKAGES

__all__ = [
    "get_template_keyboard",
    "get_modules_keyboard",
    "get_support_keyboard",
    "get_contact_keyboard",
    "get_simple_contact_keyboard",
]

def get_template_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"{tpl['name']} — {tpl['base_price']} ₽", callback_data=key)]
        for key, tpl in COST_TEMPLATES.items()
    ]
    buttons.append([InlineKeyboardButton(text="↩️ Вернуться в меню", callback_data="back_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_modules_keyboard(selected: List[str]) -> InlineKeyboardMarkup:
    keyboard = []
    for key, module in MODULES.items():
        prefix = "✅ " if key in selected else ""
        keyboard.append([
            InlineKeyboardButton(text=f"{prefix}{module['name']} (+{module['price']} ₽)", callback_data=key)
        ])
    keyboard.append([
        InlineKeyboardButton(text="↩️ Назад", callback_data="back_template"),
        InlineKeyboardButton(text="Далее", callback_data="done_modules"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_support_keyboard() -> InlineKeyboardMarkup:
    inline = [
        [InlineKeyboardButton(text=f"{pkg['name']} (+{pkg['price']} ₽)", callback_data=key)]
        for key, pkg in SUPPORT_PACKAGES.items()
    ]
    inline.append([InlineKeyboardButton(text="↩️ Назад", callback_data="back_modules")])
    return InlineKeyboardMarkup(inline_keyboard=inline)

def get_contact_keyboard(*, owner_username: str, template: str, modules: str, total: int, coupon_code: Optional[str] = None, discount: int = 0) -> InlineKeyboardMarkup:
    modules_text = modules or "-"
    lines = [
        "Приветствую!",
        "",
        "Заинтересовало создание Telegram-бота:",
        "",
        f"Шаблон: {template}",
        "Модули:",
        f"{modules_text}",
        "",
        f"Общая стоимость: {total} ₽.",
    ]
    if coupon_code:
        lines.append(f"Купон: {coupon_code} (скидка −{discount} ₽)")
    lines.extend(["", "Хотелось бы обсудить детали сотрудничества."])
    message = "\n".join(lines)
    url = f"https://t.me/{owner_username}?text=" + quote(message)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✉️ Написать мне", url=url)],
            [InlineKeyboardButton(text="↩️ Вернуться в меню", callback_data="back_menu")],
        ]
    )

def get_simple_contact_keyboard(*, owner_username: str, coupon_code: Optional[str] = None) -> InlineKeyboardMarkup:
    """Кнопка «Написать мне» с коротким, необязательным купоном."""
    lines = [
        "Приветствую!",
        "",
        "Хочу обсудить создание Telegram-бота",
    ]
    if coupon_code:
        lines.append(f"Купон: {coupon_code}")
    message = "\n".join(lines)
    url = f"https://t.me/{owner_username}?text=" + quote(message)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✉️ Написать мне", url=url)],
            [InlineKeyboardButton(text="↩️ Вернуться в меню", callback_data="back_menu")],
        ]
    ) 