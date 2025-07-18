# Виртуальный помощник Ilya Fomich — Telegram-бот

Это репозиторий исходного кода Telegram-бота, который выступает в роли **виртуального помощника Ильи Фомича**. Бот приветствует новых пользователей, показывает живые примеры проектов, объясняет выгоду от использования ботов, а также помогает рассчитать ориентировочную стоимость вашего проекта через интерактивный опрос.

> ⚠️ Проект находится на начальной стадии. Архитектура модульная, чтобы в дальнейшем было легко расширять функционал (рассылки, медиагалереи, новые калькуляторы и т. д.).

## Быстрый запуск

1. Создайте виртуальное окружение и установите зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Скопируйте файл `.env.example` в `.env` и внесите ваш `BOT_TOKEN`.
3. Поднимите локальный сервер PostgreSQL (строка подключения настраивается через `DATABASE_URL`).
4. Запустите бота:

```bash
python bot/main.py
```

## Структура проекта

```
bot/
├── config.py                  # Загрузка настроек из .env
├── main.py                    # Точка входа, запускает диспетчер aiogram
│
├── handlers/                  # Логика обработки входящих апдейтов
│   ├── start_handler.py       # Обработчик /start
│   └── navigation_menu_handlers.py  # Кнопки главного меню и калькулятор стоимости
│
├── keyboards/                 # Генераторы inline-клавиатур
│   ├── navigation_menu_keyboard.py  # Главное меню
│   └── cost_calculator_keyboard.py  # Клавиатуры мастера расчёта стоимости
│
├── services/                  # Бизнес-логика, не связанная с Telegram API
│   └── cost_calculator_service.py   # Подсчёт стоимости бота
│
├── states/                    # Определения FSM состояний
│   └── cost_calculator_states.py    # Состояния мастера калькулятора
│
└── database/
    └── connection.py          # Пул подключений к PostgreSQL (asyncpg)
```

## Расширение функционала

1. **Новые разделы меню** — добавьте файл-генератор клавиатуры в `keyboards/`, обработчики в `handlers/` и зарегистрируйте роутер в `main.py`.
2. **База данных** — создайте SQL-схемы и методы работы с ними в отдельном модуле внутри `database/`.
3. **Рассылки** — используйте `aiogram.Bot.send_message()` совместно с циклом по ID пользователей, сохранённых в БД.
4. **Медиа-контент** — для отправки изображений и видео используйте методы `bot.send_photo`, `bot.send_video` или `answer_media_group`.

## Зависимости

Список библиотек находится в `requirements.txt` (корень репозитория). Главное — `aiogram 3`, `asyncpg`, `python-dotenv`, `pydantic`.
