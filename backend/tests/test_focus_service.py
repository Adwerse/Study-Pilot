from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.models.focus_log import FocusLog
from app.schemas.focus_log import FocusSessionEnd, FocusSessionStart
from app.services.focus_service import (
    FocusConflictError,
    FocusNotFoundError,
    FocusService,
)


class FakeFocusRepository:
    def __init__(self):
        self.db = SimpleNamespace(rollback=AsyncMock())
        self.sessions: list[FocusLog] = []
        self.owned_plans: set[UUID] = set()
        self.owned_stages: dict[UUID, UUID] = {}

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
        now = datetime.now(timezone.utc)
        session = FocusLog(
            id=uuid4(),
            user_id=user_id,
            topic=topic,
            plan_id=plan_id,
            plan_stage_id=plan_stage_id,
            planned_duration_minutes=planned_duration_minutes,
            status="active",
            started_at=now,
            created_at=now,
            updated_at=now,
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

    async def get_history(
        self,
        user_id: UUID,
        session_date=None,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
    ) -> tuple[list[FocusLog], int]:
        items = [session for session in self.sessions if session.user_id == user_id]
        if status is not None:
            items = [session for session in items if session.status == status]
        if session_date is not None:
            items = [
                session
                for session in items
                if session.started_at.date() == session_date
            ]
        items = sorted(items, key=lambda item: item.started_at, reverse=True)
        return items[offset : offset + limit], len(items)

    async def get_owned_plan(self, plan_id: UUID, user_id: UUID):
        _ = user_id
        if plan_id not in self.owned_plans:
            return None
        return SimpleNamespace(id=plan_id)

    async def get_owned_stage(self, stage_id: UUID, user_id: UUID):
        _ = user_id
        plan_id = self.owned_stages.get(stage_id)
        if plan_id is None:
            return None
        return SimpleNamespace(id=stage_id, plan_id=plan_id)


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def service_and_repo():
    repo = FakeFocusRepository()
    return FocusService(repo), repo


@pytest.mark.asyncio
async def test_start_focus_session_success(service_and_repo, user_id):
    service, _ = service_and_repo

    session = await service.start_session(
        user_id=user_id,
        body=FocusSessionStart(topic="Python", planned_duration_minutes=25),
    )

    assert session.user_id == user_id
    assert session.status == "active"
    assert session.topic == "Python"
    assert session.planned_duration_minutes == 25


@pytest.mark.asyncio
async def test_cannot_start_second_active_session(service_and_repo, user_id):
    service, _ = service_and_repo
    await service.start_session(user_id=user_id, body=FocusSessionStart(topic="First"))

    with pytest.raises(FocusConflictError, match="active focus session"):
        await service.start_session(
            user_id=user_id, body=FocusSessionStart(topic="Second")
        )


@pytest.mark.asyncio
async def test_end_active_session_success(service_and_repo, user_id):
    service, _ = service_and_repo
    session = await service.start_session(
        user_id=user_id, body=FocusSessionStart(topic="Python")
    )

    ended = await service.end_session(
        user_id=user_id,
        body=FocusSessionEnd(
            session_id=session.id, status="completed", difficulty=3, notes="Good"
        ),
    )

    assert ended.status == "completed"
    assert ended.ended_at is not None
    assert ended.difficulty == 3
    assert ended.notes == "Good"


@pytest.mark.asyncio
async def test_end_session_calculates_actual_duration_seconds(
    service_and_repo, user_id
):
    service, _ = service_and_repo
    session = await service.start_session(
        user_id=user_id, body=FocusSessionStart(topic="Python")
    )
    session.started_at = datetime.now(timezone.utc) - timedelta(seconds=95)

    ended = await service.end_session(
        user_id=user_id, body=FocusSessionEnd(session_id=session.id)
    )

    assert ended.actual_duration_seconds is not None
    assert ended.actual_duration_seconds >= 95


@pytest.mark.asyncio
async def test_cannot_end_another_users_session(service_and_repo, user_id):
    service, _ = service_and_repo
    other_user_id = uuid4()
    session = await service.start_session(
        user_id=other_user_id, body=FocusSessionStart(topic="Python")
    )

    with pytest.raises(FocusNotFoundError, match="not found"):
        await service.end_session(
            user_id=user_id, body=FocusSessionEnd(session_id=session.id)
        )


@pytest.mark.asyncio
async def test_history_returns_only_current_users_sessions(service_and_repo, user_id):
    service, _ = service_and_repo
    other_user_id = uuid4()
    session = await service.start_session(
        user_id=user_id, body=FocusSessionStart(topic="Mine")
    )
    await service.start_session(
        user_id=other_user_id, body=FocusSessionStart(topic="Theirs")
    )

    history = await service.get_history(
        user_id=user_id, session_date=None, limit=20, offset=0, status=None
    )

    assert history.total == 1
    assert history.items[0].id == session.id


@pytest.mark.asyncio
async def test_history_supports_limit_and_offset(service_and_repo, user_id):
    service, _ = service_and_repo
    first = await service.start_session(
        user_id=user_id, body=FocusSessionStart(topic="First")
    )
    first.status = "completed"
    second = await service.start_session(
        user_id=user_id, body=FocusSessionStart(topic="Second")
    )
    second.status = "completed"
    third = await service.start_session(
        user_id=user_id, body=FocusSessionStart(topic="Third")
    )
    third.status = "completed"

    history = await service.get_history(
        user_id=user_id, session_date=None, limit=1, offset=1, status=None
    )

    assert history.total == 3
    assert len(history.items) == 1
    assert history.items[0].id == second.id


def test_validation_errors_for_bad_duration_and_difficulty():
    with pytest.raises(ValidationError):
        FocusSessionStart(topic="Python", planned_duration_minutes=0)

    with pytest.raises(ValidationError):
        FocusSessionStart(topic="Python", planned_duration_minutes=181)

    with pytest.raises(ValidationError):
        FocusSessionEnd(difficulty=6)
