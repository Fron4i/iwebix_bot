from typing import List

COST_TEMPLATES = {
    "schedule": {"name": "Запись/Расписание", "base_price": 25000},
    "consult": {"name": "Консультант/Продажи", "base_price": 28000},
    "creative": {"name": "Творческая студия", "base_price": 24000},
    "photo": {"name": "Фото/Видео", "base_price": 26000},
    "wellness": {"name": "Wellness & Practice", "base_price": 27000},
}

MODULES = {
    "calendar": {"name": "Интеграция календаря", "price": 5000},
    "payments": {"name": "Приём оплат", "price": 7000},
    "portfolio": {"name": "Галерея/Портфолио", "price": 4000},
    "mailing": {"name": "Рассылки и напоминания", "price": 3000},
    "loyalty": {"name": "Система лояльности", "price": 3000},
    "analytics": {"name": "Аналитика и отчётность", "price": 4000},
    "crm": {"name": "CRM-интеграция", "price": 5000},
    "documents": {"name": "Автогенерация договоров", "price": 4000},
}

SUPPORT_PACKAGES = {
    "support_6": {"name": "Поддержка 6 мес.", "price": 3000},
    "support_12": {"name": "Поддержка 12 мес.", "price": 5500},
    "no_support": {"name": "Без поддержки", "price": 0},
}


def calculate_total(*, template_key: str, module_keys: List[str], support_key: str) -> int:
    """Вычисляет итоговую стоимость проекта в рублях (фиксированные цены)."""
    template = COST_TEMPLATES[template_key]
    base = template["base_price"]
    modules_total = sum(MODULES[key]["price"] for key in module_keys)
    support_cost = SUPPORT_PACKAGES[support_key]["price"]
    return base + modules_total + support_cost 