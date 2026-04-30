from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from app.models.focus_log import FocusLog
from app.models.notification_job import NotificationJob
from app.models.user import User
from app.schemas.focus_log import FocusSessionEnd, FocusSessionStart
from app.services.focus_service import FocusService
from app.services.notification_service import NotificationService
from app.services.telegram_service import TelegramSendResult


class FakeFocusRepository:
    def __init__(self, now: datetime):
        self.db = SimpleNamespace(rollback=AsyncMock())
        self.now = now
        self.sessions: list[FocusLog] = []

    async def get_active_session(self, user_id: UUID) -> FocusLog | None:
        for session in reversed(self.sessions):
            if session.user_id == user_id and session.status == "active":
                return session
        return None

    async def create_session(
        self,
        user_id: UUID,
        topic: str | None = None,
        plan_id: UUID | None = None,
        plan_stage_id: UUID | None = None,
        planned_duration_minutes: int | None = None,
    ) -> FocusLog:
        session = FocusLog(
            id=uuid4(),
            user_id=user_id,
            topic=topic,
            plan_id=plan_id,
            plan_stage_id=plan_stage_id,
            planned_duration_minutes=planned_duration_minutes,
            status="active",
            started_at=self.now,
            created_at=self.now,
            updated_at=self.now,
        )
        self.sessions.append(session)
        return session

    async def get_by_id(
        self, session_id: UUID, user_id: UUID | None = None
    ) -> FocusLog | None:
        for session in self.sessions:
            if session.id != session_id:
                continue
            if user_id is not None and session.user_id != user_id:
                return None
            return session
        return None

    async def finish_session(
        self,
        session: FocusLog,
        status: str,
        ended_at: datetime,
        actual_duration_seconds: int,
        difficulty: int | None = None,
        notes: str | None = None,
    ) -> FocusLog:
        session.status = status
        session.ended_at = ended_at
        session.actual_duration_seconds = actual_duration_seconds
        session.difficulty = difficulty
        session.notes = notes
        session.updated_at = ended_at
        return session

    async def get_owned_plan(self, plan_id: UUID, user_id: UUID):
        _ = plan_id, user_id
        return None

    async def get_owned_stage(self, stage_id: UUID, user_id: UUID):
        _ = stage_id, user_id
        return None


class FakeNotificationRepository:
    def __init__(self):
        self.jobs: list[NotificationJob] = []
        self.sessions: dict[UUID, FocusLog] = {}
        self.users: dict[UUID, User] = {}

    async def create_job(
        self,
        *,
        user_id: UUID,
        focus_session_id: UUID,
        telegram_id: int,
        notification_type: str,
        scheduled_at: datetime,
    ) -> NotificationJob:
        now = datetime.now(timezone.utc)
        job = NotificationJob(
            id=uuid4(),
            user_id=user_id,
            focus_session_id=focus_session_id,
            telegram_id=telegram_id,
            type=notification_type,
            status="pending",
            scheduled_at=scheduled_at,
            created_at=now,
            updated_at=now,
        )
        self.jobs.append(job)
        return job

    async def cancel_pending_for_focus_session(
        self,
        focus_session_id: UUID,
        notification_type: str | None = None,
    ) -> int:
        count = 0
        for job in self.jobs:
            if job.focus_session_id != focus_session_id or job.status != "pending":
                continue
            if notification_type is not None and job.type != notification_type:
                continue
            job.status = "cancelled"
            count += 1
        return count

    async def list_due_pending(
        self,
        *,
        now: datetime,
        limit: int = 100,
    ) -> list[NotificationJob]:
        due = [
            job
            for job in self.jobs
            if job.status == "pending" and job.scheduled_at <= now
        ]
        return sorted(due, key=lambda job: job.scheduled_at)[:limit]

    async def get_focus_context(
        self, job_id: UUID
    ) -> tuple[NotificationJob, FocusLog | None, User | None] | None:
        for job in self.jobs:
            if job.id == job_id:
                return (
                    job,
                    self.sessions.get(job.focus_session_id),
                    self.users.get(job.user_id),
                )
        return None

    async def mark_sent(
        self, job: NotificationJob, sent_at: datetime | None = None
    ) -> NotificationJob:
        job.status = "sent"
        job.sent_at = sent_at or datetime.now(timezone.utc)
        job.error_message = None
        return job

    async def mark_failed(
        self, job: NotificationJob, error_message: str
    ) -> NotificationJob:
        job.status = "failed"
        job.error_message = error_message
        return job

    async def mark_cancelled(
        self, job: NotificationJob, reason: str | None = None
    ) -> NotificationJob:
        job.status = "cancelled"
        job.error_message = reason
        return job


class FakeTelegramService:
    def __init__(self, result: TelegramSendResult):
        self.result = result
        self.messages: list[dict[str, object]] = []

    async def send_message(
        self,
        telegram_id: int | str | None,
        text: str,
        parse_mode: str | None = None,
        reply_markup: dict | None = None,
    ) -> TelegramSendResult:
        self.messages.append(
            {
                "telegram_id": telegram_id,
                "text": text,
                "parse_mode": parse_mode,
                "reply_markup": reply_markup,
            }
        )
        return self.result


def build_active_session(
    *,
    user_id: UUID,
    now: datetime,
    planned_duration_minutes: int | None = 25,
    topic: str | None = "Python",
) -> FocusLog:
    return FocusLog(
        id=uuid4(),
        user_id=user_id,
        topic=topic,
        planned_duration_minutes=planned_duration_minutes,
        status="active",
        started_at=now - timedelta(minutes=25),
        created_at=now - timedelta(minutes=25),
        updated_at=now - timedelta(minutes=25),
    )


async def start_with_notifications(
    *,
    planned_duration_minutes: int | None,
    telegram_id: int | None,
) -> tuple[FocusLog, FakeNotificationRepository]:
    now = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
    focus_repo = FakeFocusRepository(now)
    notification_repo = FakeNotificationRepository()
    notification_service = NotificationService(
        notification_repo,
        telegram_service=FakeTelegramService(TelegramSendResult(success=True)),
        enabled=True,
    )
    service = FocusService(focus_repo, notification_service)

    session = await service.start_session(
        user_id=uuid4(),
        body=FocusSessionStart(
            topic="Backend",
            planned_duration_minutes=planned_duration_minutes,
        ),
        telegram_id=telegram_id,
    )
    return session, notification_repo


@pytest.mark.asyncio
async def test_start_focus_session_creates_pending_notification_job():
    session, notification_repo = await start_with_notifications(
        planned_duration_minutes=25,
        telegram_id=123456,
    )

    assert len(notification_repo.jobs) == 1
    job = notification_repo.jobs[0]
    assert job.status == "pending"
    assert job.type == "focus_end"
    assert job.user_id == session.user_id
    assert job.focus_session_id == session.id
    assert job.telegram_id == 123456


@pytest.mark.asyncio
async def test_start_focus_session_schedules_notification_at_planned_end():
    session, notification_repo = await start_with_notifications(
        planned_duration_minutes=45,
        telegram_id=123456,
    )

    assert notification_repo.jobs[0].scheduled_at == session.started_at + timedelta(
        minutes=45
    )


@pytest.mark.asyncio
async def test_start_focus_session_does_not_create_notification_without_duration():
    _, notification_repo = await start_with_notifications(
        planned_duration_minutes=None,
        telegram_id=123456,
    )

    assert notification_repo.jobs == []


@pytest.mark.asyncio
async def test_start_focus_session_does_not_create_notification_without_telegram_id():
    _, notification_repo = await start_with_notifications(
        planned_duration_minutes=25,
        telegram_id=None,
    )

    assert notification_repo.jobs == []


@pytest.mark.asyncio
async def test_end_focus_session_cancels_pending_notification_job():
    now = datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc)
    focus_repo = FakeFocusRepository(now)
    notification_repo = FakeNotificationRepository()
    notification_service = NotificationService(
        notification_repo,
        telegram_service=FakeTelegramService(TelegramSendResult(success=True)),
        enabled=True,
    )
    service = FocusService(focus_repo, notification_service)

    session = await service.start_session(
        user_id=uuid4(),
        body=FocusSessionStart(topic="Backend", planned_duration_minutes=25),
        telegram_id=123456,
    )
    await service.end_session(
        user_id=session.user_id,
        body=FocusSessionEnd(session_id=session.id, status="completed"),
    )

    assert notification_repo.jobs[0].status == "cancelled"


@pytest.mark.asyncio
async def test_process_due_notifications_sends_message_and_marks_sent():
    now = datetime.now(timezone.utc)
    user_id = uuid4()
    notification_repo = FakeNotificationRepository()
    session = build_active_session(user_id=user_id, now=now, topic="SQL")
    notification_repo.sessions[session.id] = session
    notification_repo.users[user_id] = User(id=user_id, telegram_id=123456)
    await notification_repo.create_job(
        user_id=user_id,
        focus_session_id=session.id,
        telegram_id=123456,
        notification_type="focus_end",
        scheduled_at=now - timedelta(seconds=1),
    )
    telegram = FakeTelegramService(TelegramSendResult(success=True, message_id=777))
    service = NotificationService(notification_repo, telegram, enabled=True)

    result = await service.process_due_notifications(now=now)

    assert result.sent == 1
    assert notification_repo.jobs[0].status == "sent"
    assert notification_repo.jobs[0].sent_at is not None
    assert telegram.messages[0]["telegram_id"] == 123456
    assert "Topic: SQL" in str(telegram.messages[0]["text"])


@pytest.mark.asyncio
async def test_process_due_notifications_marks_failed_on_telegram_error():
    now = datetime.now(timezone.utc)
    user_id = uuid4()
    notification_repo = FakeNotificationRepository()
    session = build_active_session(user_id=user_id, now=now)
    notification_repo.sessions[session.id] = session
    notification_repo.users[user_id] = User(id=user_id, telegram_id=123456)
    await notification_repo.create_job(
        user_id=user_id,
        focus_session_id=session.id,
        telegram_id=123456,
        notification_type="focus_end",
        scheduled_at=now - timedelta(seconds=1),
    )
    telegram = FakeTelegramService(
        TelegramSendResult(success=False, error_message="Forbidden")
    )
    service = NotificationService(notification_repo, telegram, enabled=True)

    result = await service.process_due_notifications(now=now)

    assert result.failed == 1
    assert notification_repo.jobs[0].status == "failed"
    assert notification_repo.jobs[0].error_message == "Forbidden"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["completed", "cancelled"])
async def test_process_due_notifications_does_not_send_ended_session(status: str):
    now = datetime.now(timezone.utc)
    user_id = uuid4()
    notification_repo = FakeNotificationRepository()
    session = build_active_session(user_id=user_id, now=now)
    session.status = status
    session.ended_at = now - timedelta(minutes=5)
    notification_repo.sessions[session.id] = session
    notification_repo.users[user_id] = User(id=user_id, telegram_id=123456)
    await notification_repo.create_job(
        user_id=user_id,
        focus_session_id=session.id,
        telegram_id=123456,
        notification_type="focus_end",
        scheduled_at=now - timedelta(seconds=1),
    )
    telegram = FakeTelegramService(TelegramSendResult(success=True, message_id=777))
    service = NotificationService(notification_repo, telegram, enabled=True)

    result = await service.process_due_notifications(now=now)

    assert result.cancelled == 1
    assert telegram.messages == []
    assert notification_repo.jobs[0].status == "cancelled"


@pytest.mark.asyncio
async def test_process_due_notifications_does_not_send_sent_job_twice():
    now = datetime.now(timezone.utc)
    user_id = uuid4()
    notification_repo = FakeNotificationRepository()
    session = build_active_session(user_id=user_id, now=now)
    notification_repo.sessions[session.id] = session
    notification_repo.users[user_id] = User(id=user_id, telegram_id=123456)
    await notification_repo.create_job(
        user_id=user_id,
        focus_session_id=session.id,
        telegram_id=123456,
        notification_type="focus_end",
        scheduled_at=now - timedelta(seconds=1),
    )
    telegram = FakeTelegramService(TelegramSendResult(success=True, message_id=777))
    service = NotificationService(notification_repo, telegram, enabled=True)

    await service.process_due_notifications(now=now)
    second_result = await service.process_due_notifications(now=now)

    assert second_result.processed == 0
    assert len(telegram.messages) == 1
