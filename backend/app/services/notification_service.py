import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.config import settings
from app.models.focus_log import FocusLog
from app.models.notification_job import NotificationJob
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_messages import (
    build_break_end_message,
    build_focus_end_message,
)
from app.services.telegram_service import TelegramService


logger = logging.getLogger(__name__)

FOCUS_END = "focus_end"
BREAK_END = "break_end"
PENDING = "pending"


@dataclass(frozen=True)
class NotificationProcessResult:
    processed: int = 0
    sent: int = 0
    failed: int = 0
    cancelled: int = 0


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class NotificationService:
    def __init__(
        self,
        repo: NotificationRepository,
        telegram_service: TelegramService | None = None,
        *,
        enabled: bool | None = None,
    ):
        self.repo = repo
        self.telegram_service = telegram_service or TelegramService()
        self.enabled = settings.NOTIFICATIONS_ENABLED if enabled is None else enabled

    async def schedule_focus_end_notification(
        self,
        *,
        session: FocusLog,
        telegram_id: int | str | None,
    ) -> NotificationJob | None:
        if not self.enabled:
            return None
        if not telegram_id:
            return None
        if session.planned_duration_minutes is None:
            return None

        try:
            normalized_telegram_id = int(telegram_id)
        except (TypeError, ValueError):
            logger.warning(
                "Skipping focus notification with invalid telegram_id user_id=%s "
                "focus_session_id=%s",
                session.user_id,
                session.id,
            )
            return None

        scheduled_at = ensure_utc(session.started_at) + timedelta(
            minutes=session.planned_duration_minutes
        )

        return await self.repo.create_job(
            user_id=session.user_id,
            focus_session_id=session.id,
            telegram_id=normalized_telegram_id,
            notification_type=FOCUS_END,
            scheduled_at=scheduled_at,
        )

    async def cancel_pending_focus_notifications(self, focus_session_id: UUID) -> int:
        return await self.repo.cancel_pending_for_focus_session(focus_session_id)

    async def process_due_notifications(
        self,
        *,
        now: datetime | None = None,
        limit: int = 100,
    ) -> NotificationProcessResult:
        if not self.enabled:
            return NotificationProcessResult()

        processed = sent = failed = cancelled = 0
        effective_now = ensure_utc(now or utc_now())

        for _ in range(limit):
            due_jobs = await self.repo.list_due_pending(now=effective_now, limit=1)
            if not due_jobs:
                break

            job = due_jobs[0]
            processed += 1
            outcome = await self._process_job(job)
            if outcome == "sent":
                sent += 1
            elif outcome == "cancelled":
                cancelled += 1
            else:
                failed += 1

        return NotificationProcessResult(
            processed=processed,
            sent=sent,
            failed=failed,
            cancelled=cancelled,
        )

    async def _process_job(self, job: NotificationJob) -> str:
        context = await self.repo.get_focus_context(job.id)
        if context is None:
            return "cancelled"

        current_job, session, user = context
        if current_job.status != PENDING:
            return "cancelled"

        validation_error = self._validate_context(current_job, session, user)
        if validation_error is not None:
            await self.repo.mark_cancelled(current_job, validation_error)
            logger.info(
                "Cancelled notification user_id=%s focus_session_id=%s reason=%s",
                current_job.user_id,
                current_job.focus_session_id,
                validation_error,
            )
            return "cancelled"

        message = self._build_message(current_job, session)
        if message is None:
            await self.repo.mark_failed(current_job, "Unsupported notification type")
            return "failed"

        result = await self.telegram_service.send_message(
            telegram_id=current_job.telegram_id,
            text=message,
        )

        if result.success:
            await self.repo.mark_sent(current_job, utc_now())
            logger.info(
                "Sent notification user_id=%s focus_session_id=%s message_id=%s",
                current_job.user_id,
                current_job.focus_session_id,
                result.message_id,
            )
            return "sent"

        error_message = result.error_message or "Telegram sendMessage failed"
        await self.repo.mark_failed(current_job, error_message)
        logger.warning(
            "Failed notification user_id=%s focus_session_id=%s error=%s",
            current_job.user_id,
            current_job.focus_session_id,
            error_message,
        )
        return "failed"

    def _validate_context(
        self,
        job: NotificationJob,
        session: FocusLog | None,
        user: User | None,
    ) -> str | None:
        if session is None:
            return "Focus session is missing"
        if user is None:
            return "User is missing"
        if session.user_id != job.user_id:
            return "Focus session belongs to another user"
        if user.telegram_id is None:
            return "User telegram id is missing"
        if not job.telegram_id:
            return "Notification telegram id is missing"
        if session.status != "active" or session.ended_at is not None:
            return "Focus session is no longer active"
        if job.type == FOCUS_END and session.planned_duration_minutes is None:
            return "Focus session has no planned duration"
        return None

    def _build_message(
        self, job: NotificationJob, session: FocusLog | None
    ) -> str | None:
        if job.type == BREAK_END:
            return build_break_end_message()
        if job.type == FOCUS_END and session is not None:
            if session.planned_duration_minutes is None:
                return None
            return build_focus_end_message(
                topic=session.topic,
                planned_duration_minutes=session.planned_duration_minutes,
            )
        return None
