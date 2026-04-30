from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.focus_log import FocusLog
from app.models.notification_job import NotificationJob
from app.models.user import User


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_job(
        self,
        *,
        user_id: UUID,
        focus_session_id: UUID,
        telegram_id: int,
        notification_type: str,
        scheduled_at: datetime,
    ) -> NotificationJob:
        job = NotificationJob(
            user_id=user_id,
            focus_session_id=focus_session_id,
            telegram_id=telegram_id,
            type=notification_type,
            status="pending",
            scheduled_at=scheduled_at,
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def cancel_pending_for_focus_session(
        self,
        focus_session_id: UUID,
        notification_type: str | None = None,
    ) -> int:
        filters = [
            NotificationJob.focus_session_id == focus_session_id,
            NotificationJob.status == "pending",
        ]
        if notification_type is not None:
            filters.append(NotificationJob.type == notification_type)

        result = await self.db.execute(
            update(NotificationJob)
            .where(*filters)
            .values(status="cancelled", updated_at=datetime.now(timezone.utc))
        )
        await self.db.commit()
        return int(result.rowcount or 0)

    async def list_due_pending(
        self,
        *,
        now: datetime,
        limit: int = 100,
    ) -> list[NotificationJob]:
        result = await self.db.execute(
            select(NotificationJob)
            .where(
                NotificationJob.status == "pending",
                NotificationJob.scheduled_at <= now,
            )
            .order_by(NotificationJob.scheduled_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(result.scalars().all())

    async def get_focus_context(
        self, job_id: UUID
    ) -> tuple[NotificationJob, FocusLog | None, User | None] | None:
        result = await self.db.execute(
            select(NotificationJob, FocusLog, User)
            .outerjoin(FocusLog, NotificationJob.focus_session_id == FocusLog.id)
            .outerjoin(User, NotificationJob.user_id == User.id)
            .where(NotificationJob.id == job_id)
        )
        row = result.one_or_none()
        if row is None:
            return None
        return row[0], row[1], row[2]

    async def mark_sent(
        self, job: NotificationJob, sent_at: datetime | None = None
    ) -> NotificationJob:
        job.status = "sent"
        job.sent_at = sent_at or datetime.now(timezone.utc)
        job.error_message = None
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def mark_failed(
        self, job: NotificationJob, error_message: str
    ) -> NotificationJob:
        job.status = "failed"
        job.error_message = error_message[:2000]
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def mark_cancelled(
        self, job: NotificationJob, reason: str | None = None
    ) -> NotificationJob:
        job.status = "cancelled"
        job.error_message = reason[:2000] if reason else None
        await self.db.commit()
        await self.db.refresh(job)
        return job
