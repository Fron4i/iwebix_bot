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
    "get_category_keyboard",
]

def get_category_keyboard() -> InlineKeyboardMarkup:
    categories = [
        ("services", "Услуги / Запись"),
        ("courses", "Инфопродукты / Курсы"),
        ("shop", "Интернет-магазин"),
        ("events", "Мероприятия / Билеты"),
        ("all", "Показать всё"),
    ]
    buttons = [[InlineKeyboardButton(text=label, callback_data=key)] for key, label in categories]
    # Кнопка для запроса индивидуального решения
    buttons.append([InlineKeyboardButton(text="✨ Уникальное решение", callback_data="unique_solution")])
    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="back_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_template_keyboard(category: str) -> InlineKeyboardMarkup:
    from services.cost_calculator_service import COST_TEMPLATES  # local import to avoid cycles
    mapping = {
        "services": ["schedule", "photo"],
        "courses": ["courses"],
        "shop": ["shop"],
        "events": ["tickets"],
        "all": list(COST_TEMPLATES.keys()),
    }
    keys = mapping.get(category, list(COST_TEMPLATES.keys()))
    keys_sorted = sorted(keys, key=lambda k: COST_TEMPLATES[k]["base_price"])
    buttons = [
        [InlineKeyboardButton(text=f"{COST_TEMPLATES[k]['name']} — {COST_TEMPLATES[k]['base_price']} ₽", callback_data=f"tpl_{k}")]
        for k in keys_sorted
    ]
    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="back_category")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_modules_keyboard(*, selected: List[str], template_key: str) -> InlineKeyboardMarkup:
    """Клавиатура дополнительных модулей с учётом выбранного шаблона."""
    tpl = COST_TEMPLATES.get(template_key, {})
    included = tpl.get("included", [])
    # показываем только модули, которые не входят по умолчанию
    available_keys = [k for k in MODULES if k not in included]

    keyboard = []
    for key in available_keys:
        module = MODULES[key]
        prefix = "✅ " if key in selected else ""
        keyboard.append([
            InlineKeyboardButton(text=f"{prefix}{module['name']} (+{module['price']} ₽)", callback_data=key)
        ])

    keyboard.append([
        InlineKeyboardButton(text="↩️ Назад", callback_data="back_template"),
        InlineKeyboardButton(text="👉 Далее", callback_data="done_modules"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_support_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура пакета поддержки. «Без поддержки» идёт первой."""
    order = ["no_support", "support_6", "support_12"]
    inline = [
        [InlineKeyboardButton(text=f"{SUPPORT_PACKAGES[key]['name']} (+{SUPPORT_PACKAGES[key]['price']} ₽)", callback_data=key)]
        for key in order
    ]
    inline.append([InlineKeyboardButton(text="↩️ Назад", callback_data="back_modules")])
    return InlineKeyboardMarkup(inline_keyboard=inline)

def get_contact_keyboard(*, owner_username: str, template: str, included: str, modules: str, support_line: str, total: int, coupon_code: Optional[str] = None, discount: int = 0) -> InlineKeyboardMarkup:
    """Формирует кнопку «Написать мне» с полным описанием выбора."""
    modules_text = modules or "-"
    lines = [
        "Приветствую!",
        "",
        "Заинтересовало создание Telegram-бота:",
        "",
        f"Шаблон: {template}",
    ]
    if included:
        lines.extend(["(входит):", included])

    lines.extend([
        "",
        "Модули:",
        f"{modules_text}",
        "",
        support_line,
        "",
        f"Общая стоимость: {total} ₽.",
    ])

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