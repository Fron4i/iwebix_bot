import logging
from aiogram import Router, types
import asyncio
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, InputMediaPhoto, InputMediaVideo
from urllib.parse import quote
from typing import Dict, List

# ---------------------------------------------------------------------------
# Утилита форматирования цены
# ---------------------------------------------------------------------------


def _fmt_price(value: int) -> str:
    return f"{value:,}".replace(",", " ")

from config import settings
from keyboards.navigation_menu_keyboard import get_navigation_menu
from keyboards.cost_calculator_keyboard import (
    get_template_keyboard,
    get_modules_keyboard,
    get_support_keyboard,
    get_contact_keyboard,
    get_simple_contact_keyboard,
    get_category_keyboard,
)
from keyboards.examples_keyboard import (
    get_examples_keyboard,
    get_case_keyboard,
)
from states.cost_calculator_states import CostCalculatorStates as States
from states.need_bot_game_states import NeedBotGameStates as NBStates
from services.cost_calculator_service import (
    COST_TEMPLATES,
    MODULES,
    SUPPORT_PACKAGES,
    calculate_total,
)

from database.user_repo import get_coupon, set_coupon
from database.calc_repo import get_session, upsert_session, drop_session

# Иконки для модулей
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

# Хранилище сообщений медиа по пользователю
case_media_store: Dict[int, List[types.Message]] = {}

router = Router()

# ---------------------------------------------------------------------------
# Логирование нажатий кнопок
# ---------------------------------------------------------------------------


BUTTON_TITLES = {
    "need_bot": "зачем нужен бот",
    "examples": "примеры",
    "calc_cost": "рассчитать стоимость",
    "done_modules": "далее (модули)",
    "support_6": "поддержка 6 мес.",
    "support_12": "поддержка 12 мес.",
    "no_support": "без поддержки",
    "contact_me": "написать мне",
    # динамические: шаблоны и модули
    "schedule": "шаблон запись",
    "consult": "шаблон консультант",
    "creative": "шаблон творческая",
    "photo": "шаблон фото",
    "wellness": "шаблон wellness",
    "coursebot": "шаблон курс-бот",
    "calendar": "модуль календарь",
    "payments": "модуль оплата",
    "portfolio": "модуль портфолио",
    "mailing": "модуль рассылки",
    "loyalty": "модуль лояльность",
    "crm": "модуль CRM",
    "documents": "модуль договоры",
    "back_menu": "возврат в меню",
    "back_template": "назад к выбору шаблона",
    "back_modules": "назад к модулям",
    "unique_solution": "уникальное решение",
}

# ---------------------------------------------------------------------------
# Утилиты: логирование и безопасное редактирование сообщений
# ---------------------------------------------------------------------------


def log_button(callback: types.CallbackQuery, preview_text: str) -> None:
    """Логирует нажатую кнопку и первые строки ответа."""
    username = (
        f"@{callback.from_user.username}"
        if callback.from_user.username
        else callback.from_user.full_name
    )
    title = BUTTON_TITLES.get(callback.data, callback.data)

    # Превью ограничиваем, но стараемся захватить строку с итоговой стоимостью
    lines = preview_text.split("\n")
    preview_lines = []
    for line in lines:
        preview_lines.append(line)
        if "Итоговая стоимость" in line:
            break
        if len(preview_lines) >= 25:
            break
    preview = "\n".join(preview_lines).strip()

    logging.info("%s -> %s | %s", username, title, preview)


async def safe_edit(
    message: types.Message,
    *,
    text: str,
    reply_markup=None,
    parse_mode: str | None = None,
) -> None:
    """Безопасный edit_text. Игнорируем «message is not modified»."""
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return
        raise

# ---------------------------------------------------------------------------
# Уникальное решение — сразу контакт (регистрируем рано, без state, чтобы перехватить первым)
# ---------------------------------------------------------------------------


@router.callback_query(lambda c: c.data == "unique_solution")
async def unique_solution_contact(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Сразу открывает ЛС с заполненным текстом — без промежуточного сообщения."""

    await state.clear()
    await drop_session(callback.from_user.id)

    coupon_code = await get_coupon(callback.from_user.id)
    # Формируем собственный URL с текстом «уникальное решение»
    lines = [
        "Приветствую!",
        "",
        "Хочу обсудить создание уникального Telegram-бота",
    ]
    if coupon_code:
        lines.append(f"Купон: {coupon_code}")
    message_text = "\n".join(lines)
    url = f"https://t.me/{settings.owner_username}?text=" + quote(message_text)

    # Показываем кнопку с ссылкой (надёжно, без ошибки URL_INVALID)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✉️ Написать мне", url=url)],
            [InlineKeyboardButton(text="↩️ Вернуться в меню", callback_data="back_menu")],
        ]
    )
    await safe_edit(callback.message, text="Нажмите кнопку ниже, чтобы обсудить создание уникального Telegram-бота.", reply_markup=keyboard)
    log_button(callback, "unique_solution")
    await callback.answer()


# ---------------------------------------------------------------------------
# Интерактив-викторина «Зачем нужен бот?»
# ---------------------------------------------------------------------------


QUESTIONS = [
    {
        "icon": "🤖",
        "question": "Зачем мне нужен бот?",
        "options": [
            "Стать счастливым",
            "Автоматизировать продажи",
            "Предоставить поддержку 24/7",
        ],
        "bullets": [
            "💬 отвечают на частые вопросы",
            "🛒 собирают заявки и совершают продажи",
        ],
        "conclusion": "И это всё ПОКА люди ОТДЫХАЮТ",
    },
    {
        "icon": "🎯",
        "question": "Кому могут быть полезны боты?",
        "options": [
            "Экспертам",
            "Онлайн-школам",
            "Малому бизнесу",
        ],
        "bullets": [
            "🏪 самозанятым и экспертам",
            "🎓 онлайн-курсам",
            "🏋️‍♂️ фитнес-клубам",
            "🍽 ресторанам и другим оффлайн бизнесам",
        ],
        "conclusion": "Практически любому бизнесу с повторяющимися коммуникациями",
    },
    {
        "icon": "⚙️",
        "question": "Как упрощают задачи?",
        "options": [
            "Собирают лиды",
            "Сегментируют аудиторию",
            "Автоматизируют оплаты",
        ],
        "bullets": [
            "📥 собирают лиды",
            "📊 сегментируют аудиторию",
            "💳 принимают оплаты без участия менеджера",
            "😊 ДЕЛАЮТ ВАС СЧАСТЛИВЫМИ",
        ],
        "conclusion": "Все процессы становятся быстрее и прозрачнее.",
    },
]


def build_options_keyboard(idx: int) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=opt, callback_data=f"nb_opt_{idx}")] for opt in QUESTIONS[idx]["options"]]
    buttons.append([InlineKeyboardButton(text="↩️ Вернуться в меню", callback_data="back_menu_from_needbot")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_after_answer_keyboard(idx: int) -> InlineKeyboardMarkup:
    kb = []
    if idx < len(QUESTIONS) - 1:
        kb.append([InlineKeyboardButton(text="👉 Далее", callback_data="nb_next")])
        kb.append([InlineKeyboardButton(text="↩️ Вернуться в меню", callback_data="back_menu_from_needbot")])
    else:
        kb.append([InlineKeyboardButton(text="🎁 Получить купон 5%", callback_data="need_bot_coupon")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.callback_query(lambda c: c.data == "need_bot")
async def need_bot_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(NBStates.question)
    await state.update_data(q_idx=0)
    idx = 0
    text = f"<b><i>{QUESTIONS[idx]['question']}</i></b>"
    await safe_edit(callback.message, text=text, reply_markup=build_options_keyboard(idx), parse_mode="HTML")
    log_button(callback, "need_bot_q0")
    await callback.answer()


@router.callback_query(NBStates.question, lambda c: c.data.startswith("nb_opt_"))
async def need_bot_handle_option(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    idx = data.get("q_idx", 0)
    # Build answer block
    q = QUESTIONS[idx]
    # заголовок жирный курсив + пустая строка
    lines = [f"{q['icon']} <b><i>{q['question']}</i></b>", ""]
    # специальная вводная строка для первого вопроса
    if idx == 0:
        lines.append("Боты берут на себя рутину:")
    # пункты преимущества курсивные
    bullet_lines = [f"<i>{b}</i>" for b in q["bullets"]]
    lines.extend(bullet_lines)
    lines.append("")
    # заключительная строка как код
    lines.append(f"<code>{q['conclusion']}</code>")
    answer_text = "\n".join(lines)
    await state.set_state(NBStates.answer)
    text = answer_text
    await safe_edit(callback.message, text=text, reply_markup=build_after_answer_keyboard(idx), parse_mode="HTML")
    log_button(callback, f"need_bot_answer_{idx}")
    await callback.answer()


@router.callback_query(NBStates.answer, lambda c: c.data == "nb_next")
async def need_bot_next_question(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    idx = data.get("q_idx", 0) + 1
    await state.update_data(q_idx=idx)
    await state.set_state(NBStates.question)
    text = f"<b><i>{QUESTIONS[idx]['question']}</i></b>"
    await safe_edit(callback.message, text=text, reply_markup=build_options_keyboard(idx), parse_mode="HTML")
    log_button(callback, f"need_bot_q{idx}")
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_menu_from_needbot")
async def needbot_back_menu(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit(callback.message, text="Выберите нужный пункт меню:", reply_markup=get_navigation_menu(await get_coupon(callback.from_user.id)))
    log_button(callback, "needbot_back_menu")
    await callback.answer()


@router.callback_query(NBStates.answer, lambda c: c.data == "need_bot_coupon")
async def need_bot_coupon(callback: types.CallbackQuery, state: FSMContext) -> None:
    await set_coupon(callback.from_user.id, "BOT5")
    await state.clear()
    text = (
        "🎁 Купон BOT5 активирован! При расчёте стоимости будет применена скидка 5%.\n\n"
    )
    await safe_edit(callback.message, text=text, reply_markup=get_navigation_menu(await get_coupon(callback.from_user.id)))
    log_button(callback, "need_bot_coupon")
    await callback.answer()

@router.callback_query(lambda c: c.data == "examples")
async def show_examples(callback: types.CallbackQuery) -> None:
    """Показывает список демонстрационных кейсов в одном сообщении с кнопками."""
    # Удаляем ранее отправленные медиа
    media_messages = case_media_store.get(callback.from_user.id, [])
    for msg in media_messages:
        try:
            await msg.delete()
        except Exception:
            pass
    case_media_store[callback.from_user.id] = []
    text = (
        "Ниже несколько демонстрационных проектов. Выберите интересующий кейс, "
        "чтобы увидеть подробности, фотографии/видео и ссылку на демо-бота."
    )
    try:
        await safe_edit(
            callback.message,
            text=text,
            reply_markup=get_examples_keyboard(),
        )
    except TelegramBadRequest:
        # Если исходное сообщение удалено или не может быть отредактировано — отправляем новое
        await callback.message.answer(text, reply_markup=get_examples_keyboard())
    log_button(callback, text)
    await callback.answer()


# ---------------------------------------------------------------------------
# Кейсы
# ---------------------------------------------------------------------------


@router.callback_query(lambda c: c.data == "case_shop")
async def case_shop(callback: types.CallbackQuery) -> None:
    """Карточка кейса «Магазин-бот»"""
    text = (
        "<b>🛒 Магазин-бот</b>\n\n"
        "• Быстрый старт продаж прямо в Telegram\n"
        "• Каталог товаров, корзина и оплата в несколько кликов\n"
        "• Уведомления менеджеру и клиенту\n"
    )

    # Отправляем индикатор загрузки
    loading = await callback.message.answer("⏳ Идёт загрузка кейса...")
    # Сбрасываем список медиа для последующего удаления
    case_media_store[callback.from_user.id] = []
    # Удаляем исходное сообщение с меню
    await callback.message.delete()

    # Отправляем фото и видео в одном альбоме и записываем их IDs
    media = [
        InputMediaPhoto(media=FSInputFile("media/shop.png")),
        InputMediaVideo(media=FSInputFile("media/shop.mp4")),
    ]
    # Отправляем фото и видео в одном альбоме с таймаутом
    try:
        media_messages = await asyncio.wait_for(
            callback.message.answer_media_group(media),
            timeout=10,
        )
        case_media_store[callback.from_user.id] = media_messages
    except Exception:
        # При ошибке отправки медиа показываем описание кейса без медиа
        await loading.delete()
        err_msg = await callback.message.answer("❌ не удалось загрузить медиаматериалы по кейсу")
        desc_msg = await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_case_keyboard(bot_url="https://t.me/example_shop_bot"),
        )
        case_media_store[callback.from_user.id] = [err_msg, desc_msg]
        log_button(callback, "case_shop")
        await callback.answer()
        return

    # Удаляем индикатор загрузки после небольшой задержки
    await asyncio.sleep(1)
    await loading.delete()

    # Отправляем карточку с описанием и кнопкой под медиа
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_case_keyboard(bot_url="https://t.me/example_shop_bot"),
    )
    log_button(callback, "case_shop")
    await callback.answer()


@router.callback_query(lambda c: c.data == "case_booking")
async def case_booking(callback: types.CallbackQuery) -> None:
    """Карточка кейса «Бронирование»"""
    text = (
        "<b>📆 Бронирование</b>\n\n"
        "• Онлайн-запись на услуги и мероприятия\n"
        "• Свободные окна, напоминания клиенту\n"
    )

    # Отправляем индикатор загрузки
    loading = await callback.message.answer("⏳ Идёт загрузка кейса...")
    case_media_store[callback.from_user.id] = []
    # Удаляем исходное сообщение с меню
    await callback.message.delete()

    # Отправляем фото и видео в одном альбоме
    media = [
        InputMediaPhoto(media=FSInputFile("media/booking.jpg")),
        InputMediaVideo(media=FSInputFile("media/booking.mp4")),
    ]
    try:
        media_messages = await asyncio.wait_for(
            callback.message.answer_media_group(media),
            timeout=10,
        )
        case_media_store[callback.from_user.id] = media_messages
    except Exception:
        # При ошибке отправки медиа показываем описание кейса без медиа
        await loading.delete()
        err_msg = await callback.message.answer("❌ не удалось загрузить медиаматериалы по кейсу")
        desc_msg = await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_case_keyboard(bot_url="https://t.me/example_booking_bot"),
        )
        case_media_store[callback.from_user.id] = [err_msg, desc_msg]
        log_button(callback, "case_booking")
        await callback.answer()
        return

    await asyncio.sleep(1)
    await loading.delete()

    # Отправляем карточку с описанием и кнопкой под медиа
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_case_keyboard(bot_url="https://t.me/example_booking_bot"),
    )
    log_button(callback, "case_booking")
    await callback.answer()

@router.callback_query(lambda c: c.data == "calc_cost")
async def start_calculator(callback: types.CallbackQuery, state: FSMContext) -> None:
    # persist session
    await upsert_session(callback.from_user.id, step=1)
    await state.clear()
    await state.set_state(States.choose_category)
    await callback.message.edit_text(
        "Шаг 1/4. Выберите вашу сферу деятельности:",
        reply_markup=get_category_keyboard(),
    )
    await callback.answer()
    log_button(callback, "Шаг 1/4. Выберите категорию")

# ---------------------------------------------------------------------------
# Назад из первого шага калькулятора в главное меню
# ---------------------------------------------------------------------------

# Этот обработчик нужно разместить ДО category_chosen, чтобы иметь больший приоритет
@router.callback_query(States.choose_category, lambda c: c.data == "back_menu")
async def category_back_menu_prior(callback: types.CallbackQuery, state: FSMContext) -> None:
    await calc_back_menu(callback, state)

# ------------------ category selection -----------------


@router.callback_query(States.choose_category)
async def category_chosen(callback: types.CallbackQuery, state: FSMContext) -> None:
    category_key = callback.data
    # basic validation
    valid_categories = {"services", "sales", "builder", "all"}
    if category_key not in valid_categories:
        await callback.answer("Используйте кнопки", show_alert=True)
        return
    await state.update_data(category=category_key)
    await upsert_session(callback.from_user.id, category=category_key, step=2)
    await state.set_state(States.choose_template)
    message_text = "Шаг 2/4. Выберите шаблон:"
    if category_key == "builder":
        # сразу переходим к выбору модулей
        await state.update_data(template="builder", modules=[])
        await state.set_state(States.choose_modules)
        modules_intro = (
            "Шаг 2/3. Выберите необходимые модули:\n"
            "<i>*Итоговая стоимость может отличаться от предварительной!</i>"
        )
        await safe_edit(
            callback.message,
            text=modules_intro,
            reply_markup=get_modules_keyboard(selected=[], template_key="builder"),
            parse_mode="HTML",
        )
        log_button(callback, "builder_modules")
        await callback.answer()
        return

    await safe_edit(
        callback.message,
        text=message_text,
        reply_markup=get_template_keyboard(category_key),
        parse_mode="HTML",
    )
    log_button(callback, f"выбрана категория {category_key}")
    await callback.answer()

# назад к выбору категории
@router.callback_query(States.choose_template, lambda c: c.data == "back_category")
async def back_to_category(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(States.choose_category)
    await safe_edit(
        callback.message,
        text="Шаг 1/4. Выберите вашу сферу деятельности:",
        reply_markup=get_category_keyboard(),
    )
    await callback.answer()
    log_button(callback, "назад к категориям")

# ---------------------------------------------------------------------------
# Back navigation handlers
# ---------------------------------------------------------------------------


@router.callback_query(lambda c: c.data == "back_menu")
async def calc_back_menu(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await drop_session(callback.from_user.id)
    await safe_edit(callback.message, text="Выберите нужный пункт меню:", reply_markup=get_navigation_menu(await get_coupon(callback.from_user.id)))
    log_button(callback, "возврат в меню")
    await callback.answer()


@router.callback_query(States.choose_modules, lambda c: c.data == "back_template")
async def back_to_template(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    category_key = data.get("category", "all")
    await state.set_state(States.choose_template)
    await safe_edit(
        callback.message,
        text="Шаг 2/4. Выберите шаблон:",
        reply_markup=get_template_keyboard(category_key),
    )
    log_button(callback, "назад к выбору шаблона")
    await callback.answer()


@router.callback_query(States.choose_support, lambda c: c.data == "back_modules")
async def back_to_modules(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected = data.get("modules", [])
    template_key = data.get("template")
    tpl = COST_TEMPLATES[template_key]
    included = tpl.get("included", [])

    # сформировать текст карточки, как в show_template_card
    lines = [
        f"🗂 {tpl['name']} — <b>{_fmt_price(tpl['base_price'])} ₽</b>",
        tpl["description"],
        "",
        "<b>Уже входит:</b>",
    ]
    if included:
        for m in included:
            mod = MODULES[m]
            lines.append(f"{MODULE_EMOJIS.get(m, '🧩')} {mod['name']} — {_fmt_price(mod['price'])} ₽")
    else:
        lines.append("—")

    lines.extend(["", "<i>Выберите доп модули с помощью кнопок ниже:</i>"])

    card_text = "\n".join(lines)
    await state.set_state(States.choose_modules)
    await safe_edit(
        callback.message,
        text=card_text,
        reply_markup=get_modules_keyboard(selected=selected, template_key=template_key),
        parse_mode="HTML",
    )
    log_button(callback, "назад к модулям")
    await callback.answer()
#旧 обработчик выбора шаблона отключён (конфликтовал с новой карточкой)

@router.callback_query(States.choose_modules)
async def modules_choose(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected = data.get("modules", [])

    if callback.data == "done_modules":
        await state.set_state(States.choose_support)
        support_intro = (
            "Шаг 4/4. Выберите пакет технической поддержки:\n\n"
            "🔄 Обновления контента по запросу\n"
            "🛡️ Гарантия стабильной работы\n"
            "💬 Консультация и ответы на вопросы"
        )
        await safe_edit(
            callback.message,
            text=support_intro,
            reply_markup=get_support_keyboard(),
        )
        await callback.answer()
        log_button(callback, "Шаг 4/4. Выберите пакет поддержки:")
        return
    template_key = data.get("template")
    base_allowed = [k for k in MODULES if k not in COST_TEMPLATES[template_key]["included"]]
    if template_key == "builder":
        allowed_keys = base_allowed
    elif template_key == "infobot":
        allowed_keys = [k for k in base_allowed if k in {"calendar", "mailing", "webapp", "admin_panel", "booking"}]
    else:
        allowed_keys = [k for k in base_allowed if k != "webapp_shop"]

    if callback.data not in allowed_keys:
        await callback.answer("Используйте кнопки", show_alert=True)
        return
    action = "добавлен"
    if callback.data in selected:
        selected.remove(callback.data)
        action = "удален"
    else:
        selected.append(callback.data)

    module = MODULES.get(callback.data)
    if module:
        sign = "➕" if action == "добавлен" else "➖"
        log_button(callback, f"🔧 {sign} {module['name']} ({module['price']} ₽)")
    await state.update_data(modules=selected)
    await callback.message.edit_reply_markup(reply_markup=get_modules_keyboard(selected=selected, template_key=template_key))
    await callback.answer()

@router.callback_query(States.choose_support)
async def support_chosen(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.data not in SUPPORT_PACKAGES:
        await callback.answer("Используйте кнопки", show_alert=True)
        return
    await state.update_data(support=callback.data)
    data = await state.get_data()
    if data["template"] == "builder":
        mod_total = sum((((MODULES[m]["price"] * 1.25 + 999) // 1000) * 1000) for m in data["modules"])
        total = mod_total + SUPPORT_PACKAGES[data["support"]]["price"]
    else:
        total = calculate_total(
            template_key=data["template"],
            module_keys=data["modules"],
            support_key=data["support"],
        )

    coupon_code = await get_coupon(callback.from_user.id)
    if coupon_code == "BOT5":
        discount = int(total * 0.05)
        total_after = total - discount
    else:
        discount = 0
        total_after = total

    template_key = data["template"]
    template = COST_TEMPLATES[template_key]
    template_line = f"Шаблон: <i>{template['name']}</i> — <b>{_fmt_price(template['base_price'])} ₽</b>"

    # блок включённых модулей
    incl = template.get("included", [])
    if incl:
        incl_lines = [
            f"{MODULE_EMOJIS.get(m, '🧩')} {MODULES[m]['name']} — {_fmt_price(MODULES[m]['price'])} ₽" for m in incl
        ]
        included_block = "\n".join(incl_lines)
    else:
        included_block = "—"

    if data["modules"]:
        modules_lines = []
        for m in data["modules"]:
            price = MODULES[m]["price"]
            if data.get("template") == "builder":
                price = ((int(price * 1.25 + 999)) // 1000) * 1000
            modules_lines.append(f"{MODULE_EMOJIS.get(m, '🧩')} {MODULES[m]['name']} — {_fmt_price(price)} ₽")
        modules_block = "\n".join(modules_lines)
    else:
        modules_block = "-"

    support = SUPPORT_PACKAGES[data["support"]]
    package_price = _fmt_price(support['price'])
    support_line_html = f"🤝 Пакет поддержки: <b>{support['name']}</b> (+{package_price} ₽)"
    support_line_plain = f"🤝 Пакет поддержки: {support['name']} (+{package_price} ₽)"

    summary_lines = [
        "<b>Ваш выбор:</b>",
        "",
        f"{template_line}",
        "<b>(входит):</b>",
        f"{included_block}",
        "",
        "<b>Модули:</b>",
        f"{modules_block}",
        "",
        f"{support_line_html}",
    ]

    if discount:
        summary_lines.extend(["", f"Скидка по купону <i>{coupon_code}</i>: <b>-{discount} ₽</b>"])

    summary_lines.extend(["", "", f"💰 Итоговая стоимость: <b>{_fmt_price(total_after)} ₽</b>"])

    summary = "\n".join(summary_lines)
    await safe_edit(
        callback.message,
        text=summary,
        parse_mode="HTML",
        reply_markup=get_contact_keyboard(
            owner_username=settings.owner_username,
            template=f"{template['name']} — {template['base_price']} ₽",
            included=included_block,
            modules=modules_block,
            support_line=support_line_plain,
            total=total_after,
            coupon_code=coupon_code if discount else None,
            discount=discount,
        ),
    )
    await state.clear()
    await callback.answer()
    log_button(callback, summary)


@router.callback_query(lambda c: c.data == "contact_me")
async def contact_me(callback: types.CallbackQuery) -> None:
    """Показывает кнопку для связи с автором с учётом купона."""
    coupon_code = await get_coupon(callback.from_user.id)
    keyboard = get_simple_contact_keyboard(owner_username=settings.owner_username, coupon_code=coupon_code)
    await safe_edit(callback.message, text="Нажмите кнопку ниже, чтобы связаться с автором.", reply_markup=keyboard)
    log_button(callback, "contact_me")
    await callback.answer()

# template list -> show card
@router.callback_query(States.choose_template, lambda c: c.data.startswith("tpl_") and not c.data.startswith("tpl_ok_"))
async def show_template_card(callback: types.CallbackQuery, state: FSMContext) -> None:
    template_key = callback.data.split("tpl_")[1]
    tpl = COST_TEMPLATES[template_key]
    included = tpl.get("included", [])

    # формируем текст карточки
    lines = [
        f"🗂 {tpl['name']} — <b>{_fmt_price(tpl['base_price'])} ₽</b>",
        tpl["description"],
        "",
        "<b>Уже входит:</b>",
    ]
    if included:
        for m in included:
            mod = MODULES[m]
            lines.append(f"{MODULE_EMOJIS.get(m, '🧩')} {mod['name']} — {_fmt_price(mod['price'])} ₽")
    else:
        lines.append("—")

    # Подсказка перед кнопками модулей
    lines.extend(["", "<i>Выберите доп модули с помощью кнопок ниже:</i>"])

    text = "\n".join(lines)

    # Сохраняем выбор шаблона и переходим в шаг выбора модулей (объединённый экран)
    await state.update_data(template=template_key, modules=[])
    await state.set_state(States.choose_modules)

    await safe_edit(
        callback.message,
        text=text,
        reply_markup=get_modules_keyboard(selected=[], template_key=template_key),
        parse_mode="HTML",
    )
    await callback.answer()


# confirm template — больше не используется, но оставляем для обратной совместимости
@router.callback_query(States.choose_template, lambda c: c.data.startswith("tpl_ok_"))
async def template_selected_confirm(callback: types.CallbackQuery, state: FSMContext) -> None:
    # просто перенаправляем на card-поток, чтобы не ломать старые сообщения
    new_cb = types.CallbackQuery(
        id=callback.id,
        from_user=callback.from_user,
        chat_instance=callback.chat_instance,
        message=callback.message,
        data=f"tpl_{callback.data.split('tpl_ok_')[1]}",
    )
    await show_template_card(new_cb, state)

# back_templates list
@router.callback_query(States.choose_template, lambda c: c.data == "back_templates")
async def back_templates(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    category = data.get("category", "all")
    await safe_edit(
        callback.message,
        text="Шаг 2/4. Выберите шаблон:",
        reply_markup=get_template_keyboard(category),
    )
    await callback.answer()