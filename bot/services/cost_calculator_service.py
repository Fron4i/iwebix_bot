from typing import List

COST_TEMPLATES = {
    "shop": {"name": "Магазин", "base_price": 25000},
    "booking": {"name": "Бронирование", "base_price": 30000},
    "info": {"name": "Инфо-бот", "base_price": 15000},
}

MODULES = {
    "payments": {"name": "Оплата", "price": 5000},
    "admin": {"name": "Админ-панель", "price": 8000},
    "multilang": {"name": "Мультиязык", "price": 4000},
}

SUPPORT_PACKAGES = {
    "support_6": {"name": "Поддержка 6 мес.", "multiplier": 0.1},
    "support_12": {"name": "Поддержка 12 мес.", "multiplier": 0.18},
    "no_support": {"name": "Без поддержки", "multiplier": 0.0},
}

def calculate_total(*, template_key: str, module_keys: List[str], support_key: str) -> int:
    """Вычисляет итоговую стоимость проекта в рублях."""
    template = COST_TEMPLATES[template_key]
    base = template["base_price"]
    modules_total = sum(MODULES[key]["price"] for key in module_keys)
    support = SUPPORT_PACKAGES[support_key]
    support_cost = int((base + modules_total) * support["multiplier"])
    return base + modules_total + support_cost 