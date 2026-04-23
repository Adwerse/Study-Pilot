from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.agents.focus import FocusAgent, LONG_BREAK, POMODORO_DURATION, SHORT_BREAK
from app.models.focus_log import FocusLog


@pytest.fixture
def agent():
    return FocusAgent()


@pytest.fixture
def mock_session():
    session = MagicMock(spec=FocusLog)
    session.id = uuid4()
    session.topic = "Структуры данных"
    session.started_at = datetime.now(timezone.utc)
    session.duration_minutes = 25
    return session


def test_start_message_contains_topic(agent, mock_session):
    msg = agent.format_start_message(mock_session)
    assert "Структуры данных" in msg
    assert str(POMODORO_DURATION) in msg


def test_end_message_short_break_after_first_session(agent, mock_session):
    msg = agent.format_end_message(mock_session, sessions_today=1)
    assert str(SHORT_BREAK) in msg
    assert "короткий" in msg


def test_end_message_long_break_after_fourth_session(agent, mock_session):
    msg = agent.format_end_message(mock_session, sessions_today=4)
    assert str(LONG_BREAK) in msg
    assert "длинный" in msg


def test_should_send_reminder_false_if_recent(agent):
    started = datetime.now(timezone.utc) - timedelta(minutes=20)
    assert agent.should_send_reminder(started, threshold_minutes=50) is False


def test_should_send_reminder_true_if_overdue(agent):
    started = datetime.now(timezone.utc) - timedelta(minutes=55)
    assert agent.should_send_reminder(started, threshold_minutes=50) is True
