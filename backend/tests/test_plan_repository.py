from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.plan import Plan
from app.models.plan import PlanStage
from app.repositories.plan_repository import PlanRepository


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.mark.asyncio
async def test_get_active_returns_none_when_no_plan(mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    repo = PlanRepository(mock_db)

    result = await repo.get_active_by_user(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_get_active_returns_plan_when_exists(mock_db):
    fake_plan = Plan(id=uuid4(), user_id=uuid4(), title="Test", status="active")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_plan
    mock_db.execute = AsyncMock(return_value=mock_result)
    repo = PlanRepository(mock_db)

    result = await repo.get_active_by_user(uuid4())

    assert result is not None
    assert result.title == "Test"


@pytest.mark.asyncio
async def test_update_stage_status_calls_commit(mock_db):
    mock_db.execute = AsyncMock(return_value=MagicMock())
    repo = PlanRepository(mock_db)

    await repo.update_stage_status(uuid4(), "done")

    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_stage_status_sets_completed_at_when_done(mock_db):
    stage = PlanStage(id=uuid4(), status="pending")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = stage
    mock_db.execute = AsyncMock(return_value=mock_result)
    repo = PlanRepository(mock_db)

    result = await repo.update_stage_status(uuid4(), "done")

    assert result is stage
    assert stage.status == "done"
    assert stage.completed_at is not None


@pytest.mark.asyncio
async def test_update_stage_status_clears_completed_at_when_reopened(mock_db):
    completed_at = datetime(2026, 5, 1, tzinfo=timezone.utc)
    stage = PlanStage(id=uuid4(), status="done", completed_at=completed_at)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = stage
    mock_db.execute = AsyncMock(return_value=mock_result)
    repo = PlanRepository(mock_db)

    await repo.update_stage_status(uuid4(), "pending")

    assert stage.status == "pending"
    assert stage.completed_at is None


@pytest.mark.asyncio
async def test_mark_adapted_calls_commit(mock_db):
    mock_db.execute = AsyncMock(return_value=MagicMock())
    repo = PlanRepository(mock_db)

    await repo.mark_adapted(uuid4())

    mock_db.commit.assert_called_once()
