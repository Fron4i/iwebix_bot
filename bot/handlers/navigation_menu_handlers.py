import logging
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import settings
from keyboards.navigation_menu_keyboard import get_navigation_menu
from keyboards.cost_calculator_keyboard import (
    get_template_keyboard,
    get_modules_keyboard,
    get_support_keyboard,
    get_contact_keyboard,
    get_simple_contact_keyboard,
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

# Иконки для модулей
MODULE_EMOJIS = {
    "payments": "💳",   # Оплата
    "admin": "🛠️",     # Админ-панель
    "multilang": "🌐",  # Мультиязык
}

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
    "calendar": "модуль календарь",
    "payments": "модуль оплата",
    "portfolio": "модуль портфолио",
    "mailing": "модуль рассылки",
    "loyalty": "модуль лояльность",
    "analytics": "модуль аналитика",
    "crm": "модуль CRM",
    "documents": "модуль договоры",
    "back_menu": "возврат в меню",
    "back_template": "назад к выбору шаблона",
    "back_modules": "назад к модулям",
}


def log_button(callback: types.CallbackQuery, preview_text: str) -> None:
    """Логирует кнопку и первые строки ответа, сохраняя переносы."""
    username = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name
    title = BUTTON_TITLES.get(callback.data, callback.data)

    # Формируем превью для логов так, чтобы в него обязательно вошла строка с итоговой стоимостью.
    lines = preview_text.split("\n")
    preview_lines = []
    for line in lines:
        preview_lines.append(line)
        if "Итоговая стоимость" in line:
            break  # Дошли до цены — можно остановиться
        if len(preview_lines) >= 25:  # Защита от очень длинных сообщений
            break
    preview = "\n".join(preview_lines).strip()

    logging.info("%s -> %s | %s", username, title, preview)


async def safe_edit(message: types.Message, *, text: str, reply_markup=None, parse_mode=None):
    """Edit message и залогировать первые 5 слов ответа.

    Игнорирует ошибку «message is not modified»."""
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return  # Ничего не меняем
        raise

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
    text = (
        "Ниже несколько демонстрационных проектов. Откройте любой бот и протестируйте "
        "его функциональность. В админ-панели сразу появятся результаты ваших действий."
    )
    await safe_edit(callback.message, text=text)
    log_button(callback, text)
    # При необходимости можно отправить изображения/видео отдельными сообщениями
    await callback.message.answer(
        "• Магазин-бот – t.me/example_shop_bot\n"
        "• Бронирование – t.me/example_booking_bot\n",
    )
    await callback.message.answer("Вернуться в меню:", reply_markup=get_navigation_menu(await get_coupon(callback.from_user.id)))
    await callback.answer()

@router.callback_query(lambda c: c.data == "calc_cost")
async def start_calculator(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(States.choose_template)
    await callback.message.edit_text(
        "Шаг 1/3. Выберите подходящий шаблон бота:",
        reply_markup=get_template_keyboard(),
    )
    await callback.answer()
    log_button(callback, "Шаг 1/3. Выберите подходящий шаблон бота:")

# ---------------------------------------------------------------------------
# Back navigation handlers
# ---------------------------------------------------------------------------


@router.callback_query(lambda c: c.data == "back_menu")
async def calc_back_menu(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit(callback.message, text="Выберите нужный пункт меню:", reply_markup=get_navigation_menu(await get_coupon(callback.from_user.id)))
    log_button(callback, "возврат в меню")
    await callback.answer()


@router.callback_query(States.choose_modules, lambda c: c.data == "back_template")
async def back_to_template(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(States.choose_template)
    await safe_edit(callback.message, text="Шаг 1/3. Выберите подходящий шаблон бота:", reply_markup=get_template_keyboard())
    log_button(callback, "назад к выбору шаблона")
    await callback.answer()


@router.callback_query(States.choose_support, lambda c: c.data == "back_modules")
async def back_to_modules(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected = data.get("modules", [])
    await state.set_state(States.choose_modules)
    await safe_edit(callback.message, text="Шаг 2/3. Выберите необходимые модули (можно несколько):", reply_markup=get_modules_keyboard(selected=selected))
    log_button(callback, "назад к модулям")
    await callback.answer()

@router.callback_query(States.choose_template)
async def template_chosen(callback: types.CallbackQuery, state: FSMContext) -> None:
    template_key = callback.data
    if template_key not in COST_TEMPLATES:
        await callback.answer("Используйте кнопки", show_alert=True)
        return
    await state.update_data(template=template_key, modules=[])
    await state.set_state(States.choose_modules)
    tpl = COST_TEMPLATES[template_key]
    log_button(callback, f"🏷️ Шаблон выбран: {tpl['name']} — {tpl['base_price']} ₽")
    await callback.message.edit_text(
        "Шаг 2/3. Выберите необходимые модули (можно несколько):",
        reply_markup=get_modules_keyboard(selected=[]),
    )
    await callback.answer()

@router.callback_query(States.choose_modules)
async def modules_choose(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected = data.get("modules", [])

    if callback.data == "done_modules":
        await state.set_state(States.choose_support)
        await safe_edit(
            callback.message,
            text="Шаг 3/3. Выберите пакет поддержки:",
            reply_markup=get_support_keyboard(),
        )
        await callback.answer()
        log_button(callback, "Шаг 3/3. Выберите пакет поддержки:")
        return
    if callback.data not in MODULES:
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
    await callback.message.edit_reply_markup(reply_markup=get_modules_keyboard(selected=selected))
    await callback.answer()

@router.callback_query(States.choose_support)
async def support_chosen(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.data not in SUPPORT_PACKAGES:
        await callback.answer("Используйте кнопки", show_alert=True)
        return
    await state.update_data(support=callback.data)
    data = await state.get_data()
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
    template_line = f"🗂️ Шаблон: {template['name']} — {template['base_price']} ₽"

    if data["modules"]:
        modules_lines = [
            f"{MODULE_EMOJIS.get(m, '🧩')} {MODULES[m]['name']} — {MODULES[m]['price']} ₽" for m in data["modules"]
        ]
        modules_block = "\n".join(modules_lines)
    else:
        modules_block = "-"

    support = SUPPORT_PACKAGES[data["support"]]
    support_line = f"🤝 Пакет поддержки: {support['name']} (+{support['price']} ₽)"

    summary_lines = [
        "Ваш выбор:",
        "",
        "",
        f"{template_line}",
        "",
        f"Модули:",
        f"{modules_block}",
        "",
        f"{support_line}",
    ]

    if discount:
        summary_lines.extend(["", f"Скидка по купону BOT5: -{discount} ₽"])

    summary_lines.extend(["", "", f"💰 Итоговая стоимость: *{total_after} ₽*"])

    summary = "\n".join(summary_lines)
    await safe_edit(
        callback.message,
        text=summary,
        parse_mode="Markdown",
        reply_markup=get_contact_keyboard(
            owner_username=settings.owner_username,
            template=f"{template['name']} — {template['base_price']} ₽",
            modules=modules_block,
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