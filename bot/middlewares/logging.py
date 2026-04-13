import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update


logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        update_type = self._get_update_type(event)
        telegram_id = self._get_telegram_id(event)
        message_preview = self._get_message_preview(event)

        logger.info(
            "Incoming update type=%s telegram_id=%s text=%s",
            update_type,
            telegram_id,
            message_preview,
        )

        return await handler(event, data)

    @staticmethod
    def _get_update_type(event: TelegramObject) -> str:
        if isinstance(event, Update):
            return event.event_type
        if isinstance(event, Message):
            return "message"
        if isinstance(event, CallbackQuery):
            return "callback"
        return event.__class__.__name__.lower()

    @staticmethod
    def _get_telegram_id(event: TelegramObject) -> int | None:
        from_user = getattr(event, "from_user", None)
        if from_user is not None:
            return from_user.id

        if isinstance(event, Update):
            user = event.event.from_user if hasattr(event, "event") and event.event else None
            if user is not None:
                return user.id

        return None

    @staticmethod
    def _get_message_preview(event: TelegramObject) -> str | None:
        text: str | None = None

        if isinstance(event, Message):
            text = event.text or event.caption
        elif isinstance(event, CallbackQuery):
            text = event.data
        elif isinstance(event, Update) and hasattr(event, "event") and event.event:
            nested_event = event.event
            text = getattr(nested_event, "text", None) or getattr(nested_event, "caption", None)

        if not text:
            return None
        return text[:50]