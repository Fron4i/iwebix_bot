from typing import List

COST_TEMPLATES = {
    "infobot": {
        "name": "Инфо-бот",
        "base_price": 20000,
        "description": "Автоматически отвечает на вопросы, показывает портфолио и принимает заявки 24/7.",
        "included": ["portfolio", "loyalty", "quest"],
    },
    "tickets": {
        "name": "Продажа билетов",
        "base_price": 25000,
        "description": "Онлайн-продажа билетов и мест на мероприятия прямо в Telegram.",
        "included": ["admin_panel", "mailing"],
    },
    "schedule": {
        "name": "Запись/Расписание",
        "base_price": 30000,
        "description": "Автоматическая запись клиентов, свободные слоты и напоминания.",
        "included": ["calendar", "loyalty"],
    },
    "courses": {
        "name": "Продажа курсов",
        "base_price": 30000,
        "description": "Сбор лидов, продажа обучающих программ и рассылки.",
        "included": ["calendar", "mailing", "loyalty"],
    },
    "photo": {
        "name": "Фото/Видео",
        "base_price": 26000,
        "description": "Портфолио и бронирование дат для съёмок.",
        "included": ["portfolio"],
    },
    "shop": {
        "name": "Интернет-магазин",
        "base_price": 45000,
        "description": "Полноценные продажи товаров в Telegram с оплатой и админкой.",
        "included": ["payments", "portfolio", "mailing", "loyalty", "crm", "admin_panel"],
    },
}

MODULES = {
    "calendar": {"name": "Интеграция календаря", "price": 5000, "desc": "Связь с Google/Outlook, свободные слоты."},
    "payments": {"name": "Приём оплат", "price": 7000, "desc": "Stripe, ЮKassa, СБП."},
    "portfolio": {"name": "Галерея/Портфолио", "price": 4000, "desc": "Красивый показ работ."},
    "mailing": {"name": "Рассылки и напоминания", "price": 3000, "desc": "Авторассылки, push-напоминания."},
    "loyalty": {"name": "Система лояльности", "price": 3000, "desc": "Купоны, баллы и кэшбэк."},
    "analytics": {"name": "Аналитика и отчётность", "price": 4000, "desc": "Статистика и выгрузки."},
    "crm": {"name": "CRM-интеграция", "price": 5000, "desc": "Передаёт лиды в Amo/B24."},
    "documents": {"name": "Автогенерация договоров", "price": 4000, "desc": "PDF договор с данными клиента."},
    "webapp": {"name": "Telegram Web-App", "price": 10000, "desc": "Удобная витрина внутри TG."},
    "webapp_shop": {"name": "Web-App витрина", "price": 12000, "desc": "Каталог товара в Web-App."},
    "quest": {"name": "Квест-игра", "price": 3000, "desc": "Игровой сценарий с бонусом"},
    "admin_panel": {"name": "Админ-панель", "price": 6000, "desc": "Управление контентом/заказами."},
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