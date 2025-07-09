import logging
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from config import settings
from keyboards.navigation_menu_keyboard import get_navigation_menu
from keyboards.cost_calculator_keyboard import (
    get_template_keyboard,
    get_modules_keyboard,
    get_support_keyboard,
    get_contact_keyboard,
)
from states.cost_calculator_states import CostCalculatorStates as States
from services.cost_calculator_service import (
    COST_TEMPLATES,
    MODULES,
    SUPPORT_PACKAGES,
    calculate_total,
)

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
    "shop": "шаблон магазин",
    "booking": "шаблон бронирование",
    "info": "шаблон инфо-бот",
    "payments": "модуль оплата",
    "admin": "модуль админ",
    "multilang": "модуль мультиязык",
    "back_menu": "возврат в меню",
    "back_template": "назад к выбору шаблона",
    "back_modules": "назад к модулям",
}


def log_button(callback: types.CallbackQuery, preview_text: str) -> None:
    """Логирует кнопку и первые строки ответа, сохраняя переносы."""
    username = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name
    title = BUTTON_TITLES.get(callback.data, callback.data)

    # Оставляем максимум 6 строк для превью
    lines = preview_text.split("\n")
    preview = "\n".join(lines[:10]).strip()

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

@router.callback_query(lambda c: c.data == "need_bot")
async def explain_need_bot(callback: types.CallbackQuery) -> None:
    content = (
        "Telegram-боты помогают автоматизировать продажи, поддержку и маркетинг. "
        "Они доступны 24/7, мгновенно отвечают на запросы и интегрируются с CRM, «1С» "
        "и другими системами. Используя ботов, компании снижают нагрузку на менеджеров "
        "и повышают лояльность клиентов."
    )
    await safe_edit(callback.message, text=content, reply_markup=get_navigation_menu())
    log_button(callback, content)
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
    await callback.message.answer("Вернуться в меню:", reply_markup=get_navigation_menu())
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
    await safe_edit(callback.message, text="Выберите нужный пункт меню:", reply_markup=get_navigation_menu())
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
    template_key = data["template"]
    template = COST_TEMPLATES[template_key]
    template_line = f"Шаблон: {template['name']} — {template['base_price']} ₽"

    if data["modules"]:
        modules_lines = [f"{MODULES[m]['name']} — {MODULES[m]['price']} ₽" for m in data["modules"]]
        modules_block = "\n".join(modules_lines)
    else:
        modules_block = "-"

    support = SUPPORT_PACKAGES[data["support"]]
    support_line = f"Пакет поддержки: {support['name']} (+{int(support['multiplier']*100)}%)"

    summary = (
        "Ваш выбор:\n\n"
        f"{template_line}\n\n"
        f"Модули:\n{modules_block}\n\n"
        f"{support_line}\n\n"
        f"Итоговая стоимость: **{total} ₽**"
    )
    await safe_edit(
        callback.message,
        text=summary,
        parse_mode="Markdown",
        reply_markup=get_contact_keyboard(
            owner_username=settings.owner_username,
            template=template['name'],
            modules=modules_block.replace('\n', ', '),
            total=total,
        ),
    )
    await state.clear()
    await callback.answer()
    log_button(callback, summary)


@router.callback_query(lambda c: c.data == "contact_me")
async def contact_me(callback: types.CallbackQuery) -> None:
    """Отправляет ссылку для связи с автором."""
    text = (
        "Отлично! Свяжитесь с автором, чтобы обсудить детали – "
        f"https://t.me/{settings.owner_username}"
    )
    await safe_edit(callback.message, text=text, reply_markup=get_navigation_menu())
    log_button(callback, text)
    await callback.answer()