import logging
from aiogram import BaseMiddleware, types
from typing import Callable, Any, Dict

class InteractionLoggingMiddleware(BaseMiddleware):
    """Middleware пишет в лог, какие сообщения и callback нажимал пользователь."""

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Any],
        event: types.TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        username = f"@{event.from_user.username}" if event.from_user.username else event.from_user.full_name

        if isinstance(event, types.Message):
            result = await handler(event, data)
            text = event.text or ""
            lines = text.split("\n")
            preview = "\n".join(lines[:10]).strip()
            logging.info("%s -> сообщение | %s", username, preview)
            return result
        # callbacks логируются в самих хендлерах
        return await handler(event, data) 