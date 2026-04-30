import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TelegramSendResult:
    success: bool
    message_id: int | None = None
    error_message: str | None = None


class TelegramService:
    def __init__(
        self,
        *,
        bot_token: str | None = None,
        timeout_seconds: float = 10.0,
    ):
        self.bot_token = (
            bot_token if bot_token is not None else settings.telegram_bot_token
        )
        self.timeout_seconds = timeout_seconds

    async def send_message(
        self,
        telegram_id: int | str | None,
        text: str,
        parse_mode: str | None = None,
        reply_markup: dict[str, Any] | None = None,
    ) -> TelegramSendResult:
        if not telegram_id:
            return TelegramSendResult(
                success=False,
                error_message="Telegram id is missing",
            )

        if not self.bot_token:
            logger.warning("Telegram notification skipped: bot token is not configured")
            return TelegramSendResult(
                success=False,
                error_message="Telegram bot token is not configured",
            )

        payload: dict[str, Any] = {
            "chat_id": telegram_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload)
        except httpx.HTTPError as exc:
            logger.warning("Telegram sendMessage request failed: %s", exc)
            return TelegramSendResult(success=False, error_message=str(exc))

        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code >= 400 or not data.get("ok", False):
            description = data.get("description")
            error_message = (
                str(description)
                if description
                else f"Telegram API returned HTTP {response.status_code}"
            )
            logger.warning(
                "Telegram sendMessage failed with status %s: %s",
                response.status_code,
                error_message,
            )
            return TelegramSendResult(success=False, error_message=error_message)

        result = data.get("result") if isinstance(data, dict) else None
        message_id = result.get("message_id") if isinstance(result, dict) else None
        return TelegramSendResult(success=True, message_id=message_id)
