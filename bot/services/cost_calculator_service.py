from typing import List

COST_TEMPLATES = {
    "infobot": {
        "name": "Информационный-бот",
        "base_price": 20000,
        "description": "Автоматически отвечает на вопросы, представляет портфолио 24/7",
        "included": ["portfolio", "quest"],
    },
    "tickets": {
        "name": "Продажа билетов",
        "base_price": 30000,
        "base_price": 30000,
        "description": "Онлайн-продажа билетов и мест на мероприятия прямо в Telegram",
        "included": ["admin_panel", "booking", "mailing", "calendar", "portfolio","quest"],
    },
    "schedule": {
        "name": "Продажа услуг (запись)",
        "base_price": 35000,
        "description": "Автоматическая запись клиентов, свободные окна, напоминания, аналитика в админке",
        "included": ["admin_panel", "calendar", "portfolio", "mailing",  "loyalty","quest"],
    },
    "courses": {
        "name": "Продажа курсов",
        "base_price": 35000,
        "description": "Демонстрация продукта, продажа обучающих программ и напоминания",
        "included": ["admin_panel", "calendar", "mailing", "loyalty", "portfolio", "quest"],
    },
    "photo": {
        "name": "Все для фото-видиографа",
        "base_price": 30000,
        "description": "Демонстрация портфолио, бронирование дат для съёмок, напоминания",
        "included": ["booking","portfolio", "calendar", "mailing", "loyalty", "quest"],
    },
    "coursebot": {
        "name": "Создание курса-бота",
        "base_price": 40000,
        "description": "Проведение обучающих программ в формате чат-бота: уроки, тесты, сертификаты",
        "included": ["admin_panel", "documents", "calendar", "mailing","portfolio", "loyalty", "quest"],
    },
    "shop": {
        "name": "Интернет-магазин",
        "base_price": 45000,
        "description": "Полноценные продажи товаров в Telegram с оплатой и админкой",
        "included": ["payments", "portfolio", "mailing", "loyalty", "crm", "admin_panel"],
    },
    "builder": {
        "name": "Собрать модульно",
        "base_price": 0,
        "description": "Конструктор проекта — выберите нужные модули",
        "included": [],
    },
}

MODULES = {
    "calendar": {"name": "Расписание мероприятий", "price": 4000, "desc": "События, слоты, напоминания."},
    "booking": {"name": "Онлайн-запись", "price": 5000, "desc": "Онлайн-запись с выбором времени."},
    "payments": {"name": "Роботизированные оплаты", "price": 7000, "desc": "Stripe, ЮKassa, СБП."},
    "portfolio": {"name": "Галерея/Портфолио", "price": 4000, "desc": "Красивый показ работ."},
    "mailing": {"name": "Рассылки и напоминания", "price": 4000, "desc": "Авторассылки, push-напоминания."},
    "loyalty": {"name": "Система лояльности", "price": 3000, "desc": "Купоны, баллы и кэшбэк."},
    "crm": {"name": "CRM-интеграция", "price": 5000, "desc": "Передаёт лиды в Amo/B24."},
    "documents": {"name": "Автогенерация документов", "price": 5000, "desc": "PDF договор с данными клиента."},
    "webapp": {"name": "Web-App приложение", "price": 10000, "desc": "Кастомное приложение внутри Telegram."},
    "webapp_shop": {"name": "Web-App витрина", "price": 12000, "desc": "Каталог товара в Web-App."},
    "quest": {"name": "Лид-магнит (квест-игра)", "price": 3000, "desc": "Игровой сценарий с бонусом"},
    "admin_panel": {"name": "Админ-панель с аналитикой", "price": 6000, "desc": "Управление + статистика."},
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