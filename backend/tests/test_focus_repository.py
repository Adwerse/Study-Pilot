from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.focus_log import FocusLog
from app.repositories.focus_repository import FocusRepository


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.mark.asyncio
async def test_get_active_returns_none_when_no_session(mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    repo = FocusRepository(mock_db)
    result = await repo.get_active_session(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_start_session_calls_add_and_commit(mock_db):
    async def mock_refresh(obj):
        obj.id = uuid4()

    mock_db.refresh = mock_refresh
    repo = FocusRepository(mock_db)
    await repo.start_session(user_id=uuid4(), topic="Python")
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_end_session_returns_none_if_not_found(mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    repo = FocusRepository(mock_db)
    result = await repo.end_session(uuid4(), difficulty=3)
    assert result is None
