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

# ---------------------------------------------------------------------------
# Утилита форматирования цены: 20000 -> 20 000
# ---------------------------------------------------------------------------


def _fmt_price(value: int) -> str:
    return f"{value:,}".replace(",", " ")


# Эмодзи для модулей (должны быть объявлены до функций)
MODULE_EMOJIS = {
    "calendar": "🗓️",
    "payments": "💳",
    "portfolio": "🖼️",
    "mailing": "📧",
    "loyalty": "🎁",
    "crm": "📋",
    "documents": "📄",
    "webapp": "🌐",
    "webapp_shop": "🛒",
    "quest": "🎲",
    "admin_panel": "🛠️",
    "booking": "📆",
}

# Эмодзи для шаблонов
TEMPLATE_EMOJIS = {
    "infobot": "🤖",
    "tickets": "🎟️",
    "schedule": "📆",
    "courses": "📚",
    "photo": "📷",
    "coursebot": "🎓",
    "shop": "🛒",
    "builder": "🧩",
}

# Эмодзи для пакетов поддержки
SUPPORT_EMOJIS = {
    "no_support": "🚫",
    "support_6": "��️",
    "support_12": "🛡️",
}


def get_category_keyboard() -> InlineKeyboardMarkup:
    categories = [
        ("all", "🗂️ Показать всё"),
        ("builder", "🧩 Собрать помодульно"),
        ("services", "💼 Предоставление услуг (Эксперт)"),
        ("sales", "🛒 Продажи (мероприятия, курсы, товары)"),
    ]
    buttons = [[InlineKeyboardButton(text=label, callback_data=key)] for key, label in categories]
    # Кнопка для запроса индивидуального решения
    buttons.append([InlineKeyboardButton(text="✨ Хочу уникальное решение", callback_data="unique_solution")])
    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="back_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_template_keyboard(category: str) -> InlineKeyboardMarkup:
    from services.cost_calculator_service import COST_TEMPLATES  # local import to avoid cycles
    mapping = {
        "services": ["infobot", "photo", "schedule", "coursebot"],
        "sales": ["tickets", "courses", "shop"],
        "builder": list(COST_TEMPLATES.keys()),  # отображаем все, пользователь соберёт сам
        "all": list(COST_TEMPLATES.keys()),
    }
    keys = mapping.get(category, list(COST_TEMPLATES.keys()))
    keys_sorted = sorted(keys, key=lambda k: COST_TEMPLATES[k]["base_price"])
    buttons = []
    for k in keys_sorted:
        tpl = COST_TEMPLATES[k]
        emoji = TEMPLATE_EMOJIS.get(k, "📂")
        text = f"{emoji} {tpl['name']} — {_fmt_price(tpl['base_price'])} ₽"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"tpl_{k}")])
    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="back_category")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_modules_keyboard(*, selected: List[str], template_key: str) -> InlineKeyboardMarkup:
    """Клавиатура дополнительных модулей с учётом выбранного шаблона."""
    tpl = COST_TEMPLATES.get(template_key, {})
    included = tpl.get("included", [])
    # показываем только модули, которые не входят по умолчанию
    # дополнительная фильтрация webapp / webapp_shop
    if template_key == "shop":
        # для магазина скрываем обычный webapp, оставляем витрину
        available_keys = [k for k in MODULES if k not in included and k != "webapp"]
    elif template_key == "infobot":
        allowed_set = {"calendar", "mailing", "webapp", "admin_panel", "booking"}
        available_keys = [k for k in MODULES if k in allowed_set and k not in included]
    else:
        # для остальных скрываем витрину
        available_keys = [k for k in MODULES if k not in included and k != "webapp_shop"]

    # сортируем по цене
    available_keys = sorted(available_keys, key=lambda x: MODULES[x]["price"])

    keyboard = []
    for key in available_keys:
        module = MODULES[key]
        prefix = "✅ " if key in selected else ""
        emoji = MODULE_EMOJIS.get(key, "🧩")
        price = module["price"]
        if template_key == "builder":
            price = ((int(price * 1.2 + 999)) // 1000) * 1000  # 20% и округление вверх до 1000
        keyboard.append([
            InlineKeyboardButton(text=f"{prefix}{emoji} {module['name']} (+{_fmt_price(price)} ₽)", callback_data=key)
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
        [
            InlineKeyboardButton(
                text=f"{SUPPORT_EMOJIS.get(key, '🤝')} {SUPPORT_PACKAGES[key]['name']} (+{_fmt_price(SUPPORT_PACKAGES[key]['price'])} ₽)",
                callback_data=key,
            )
        ]
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