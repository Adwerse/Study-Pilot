from datetime import date, datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.models.focus_log import FocusLog
from app.services.analytics_metrics_service import (
    AnalyticsMetricsService,
    UNTITLED_TOPIC,
)


UTC = timezone.utc


class FakeFocusRepository:
    def __init__(self, sessions: list[FocusLog]):
        self.sessions = sessions

    async def list_sessions_between(
        self,
        user_id: UUID,
        start_utc: datetime,
        end_utc: datetime,
        statuses=None,
    ) -> list[FocusLog]:
        selected_statuses = set(statuses or [])
        return [
            session
            for session in self.sessions
            if session.user_id == user_id
            and session.started_at >= start_utc
            and session.started_at < end_utc
            and (not selected_statuses or session.status in selected_statuses)
        ]

    async def list_completed_sessions_until(
        self,
        user_id: UUID,
        end_utc: datetime,
    ) -> list[FocusLog]:
        return [
            session
            for session in self.sessions
            if session.user_id == user_id
            and session.status == "completed"
            and (session.actual_duration_seconds or 0) > 0
            and session.started_at < end_utc
        ]


class FakePlanRepository:
    def __init__(self, plan=None):
        self.plan = plan

    async def get_active_by_user(self, user_id: UUID):
        _ = user_id
        return self.plan


def make_service(
    sessions: list[FocusLog],
    plan=None,
) -> AnalyticsMetricsService:
    return AnalyticsMetricsService(
        focus_repo=FakeFocusRepository(sessions),
        plan_repo=FakePlanRepository(plan),
    )


def make_session(
    *,
    user_id: UUID,
    started_at: datetime,
    status: str = "completed",
    seconds: int | None = 1500,
    topic: str | None = "Python",
) -> FocusLog:
    return FocusLog(
        id=uuid4(),
        user_id=user_id,
        status=status,
        started_at=started_at,
        actual_duration_seconds=seconds,
        topic=topic,
    )


@pytest.mark.asyncio
async def test_daily_metrics_count_only_completed_focus_time() -> None:
    user_id = uuid4()
    other_user_id = uuid4()
    service = make_service(
        [
            make_session(
                user_id=user_id,
                started_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
                seconds=1800,
                topic="FastAPI",
            ),
            make_session(
                user_id=user_id,
                started_at=datetime(2026, 5, 1, 14, 0, tzinfo=UTC),
                seconds=1500,
                topic="PostgreSQL",
            ),
            make_session(
                user_id=user_id,
                started_at=datetime(2026, 5, 1, 15, 0, tzinfo=UTC),
                status="cancelled",
                seconds=3600,
                topic="Cancelled",
            ),
            make_session(
                user_id=other_user_id,
                started_at=datetime(2026, 5, 1, 11, 0, tzinfo=UTC),
                seconds=7200,
                topic="Other user",
            ),
        ]
    )

    result = await service.build_daily_report(
        user_id=user_id,
        report_date=date(2026, 5, 1),
        user_timezone=ZoneInfo("UTC"),
    )

    assert result.metrics.total_focus_seconds == 3300
    assert result.metrics.total_focus_minutes == 55
    assert result.metrics.sessions_count == 2
    assert result.metrics.cancelled_sessions_count == 1
    assert result.metrics.completion_rate == 67
    assert result.metrics.average_session_minutes == 28


@pytest.mark.asyncio
async def test_empty_metrics_handle_zero_denominator_and_average() -> None:
    result = await make_service([]).build_daily_report(
        user_id=uuid4(),
        report_date=date(2026, 5, 1),
        user_timezone=ZoneInfo("UTC"),
    )

    assert result.metrics.total_focus_minutes == 0
    assert result.metrics.sessions_count == 0
    assert result.metrics.completion_rate == 0
    assert result.metrics.average_session_minutes is None
    assert result.data_quality.value == "low"


@pytest.mark.asyncio
async def test_streak_counts_consecutive_completed_days_only() -> None:
    user_id = uuid4()
    sessions = [
        make_session(
            user_id=user_id,
            started_at=datetime(2026, 5, 4, 9, 0, tzinfo=UTC),
        ),
        make_session(
            user_id=user_id,
            started_at=datetime(2026, 5, 5, 9, 0, tzinfo=UTC),
        ),
        make_session(
            user_id=user_id,
            started_at=datetime(2026, 5, 7, 9, 0, tzinfo=UTC),
        ),
        make_session(
            user_id=user_id,
            started_at=datetime(2026, 5, 8, 9, 0, tzinfo=UTC),
            status="cancelled",
        ),
    ]
    service = make_service(sessions)

    tuesday = await service.build_daily_report(
        user_id=user_id,
        report_date=date(2026, 5, 5),
        user_timezone=ZoneInfo("UTC"),
    )
    friday = await service.build_daily_report(
        user_id=user_id,
        report_date=date(2026, 5, 8),
        user_timezone=ZoneInfo("UTC"),
    )

    assert tuesday.metrics.streak_days == 2
    assert friday.metrics.streak_days == 0


@pytest.mark.asyncio
async def test_streak_ignores_zero_duration_completed_sessions() -> None:
    user_id = uuid4()
    service = make_service(
        [
            make_session(
                user_id=user_id,
                started_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
                seconds=0,
            )
        ]
    )

    result = await service.build_daily_report(
        user_id=user_id,
        report_date=date(2026, 5, 1),
        user_timezone=ZoneInfo("UTC"),
    )

    assert result.metrics.sessions_count == 1
    assert result.metrics.streak_days == 0


@pytest.mark.asyncio
async def test_best_focus_hours_group_by_local_timezone() -> None:
    user_id = uuid4()
    service = make_service(
        [
            make_session(
                user_id=user_id,
                started_at=datetime(2026, 5, 1, 8, 0, tzinfo=UTC),
                seconds=1800,
            ),
            make_session(
                user_id=user_id,
                started_at=datetime(2026, 5, 1, 8, 45, tzinfo=UTC),
                seconds=1800,
            ),
            make_session(
                user_id=user_id,
                started_at=datetime(2026, 5, 1, 13, 0, tzinfo=UTC),
                seconds=7200,
            ),
        ]
    )

    result = await service.build_daily_report(
        user_id=user_id,
        report_date=date(2026, 5, 1),
        user_timezone=ZoneInfo("Europe/Dublin"),
    )

    assert result.metrics.best_focus_hours[:2] == ["14:00", "09:00"]


@pytest.mark.asyncio
async def test_most_focused_topics_aggregate_minutes_with_untitled_topic() -> None:
    user_id = uuid4()
    service = make_service(
        [
            make_session(
                user_id=user_id,
                started_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
                seconds=600,
                topic="RAG",
            ),
            make_session(
                user_id=user_id,
                started_at=datetime(2026, 5, 1, 11, 0, tzinfo=UTC),
                seconds=1200,
                topic=None,
            ),
        ]
    )

    result = await service.build_daily_report(
        user_id=user_id,
        report_date=date(2026, 5, 1),
        user_timezone=ZoneInfo("UTC"),
    )

    assert result.metrics.most_focused_topics[0].topic == UNTITLED_TOPIC
    assert result.metrics.most_focused_topics[0].minutes == 20
    assert result.metrics.most_focused_topics[1].topic == "RAG"


@pytest.mark.asyncio
async def test_weekly_daily_breakdown_contains_all_days() -> None:
    user_id = uuid4()
    service = make_service(
        [
            make_session(
                user_id=user_id,
                started_at=datetime(2026, 4, 27, 9, 0, tzinfo=UTC),
                seconds=3600,
            ),
            make_session(
                user_id=user_id,
                started_at=datetime(2026, 4, 27, 18, 0, tzinfo=UTC),
                status="cancelled",
            ),
            make_session(
                user_id=user_id,
                started_at=datetime(2026, 4, 28, 10, 0, tzinfo=UTC),
                seconds=1800,
            ),
        ]
    )

    result = await service.build_weekly_report(
        user_id=user_id,
        week_start=date(2026, 4, 29),
        user_timezone=ZoneInfo("UTC"),
    )

    assert result.period.start.date() == date(2026, 4, 27)
    assert len(result.daily_breakdown or []) == 7
    assert result.daily_breakdown[0].focus_minutes == 60
    assert result.daily_breakdown[0].sessions_count == 1
    assert result.daily_breakdown[0].completion_rate == 50
    assert result.daily_breakdown[1].focus_minutes == 30
    assert result.daily_breakdown[-1].focus_minutes == 0


@pytest.mark.asyncio
async def test_plan_progress_uses_active_plan_stages() -> None:
    user_id = uuid4()
    plan = SimpleNamespace(
        id=uuid4(),
        title="Backend Plan",
        stages=[
            SimpleNamespace(id=uuid4(), status="done", title="SQL", order_index=0),
            SimpleNamespace(
                id=uuid4(),
                status="in_progress",
                title="Analytics",
                order_index=1,
            ),
        ],
    )
    service = make_service([], plan=plan)

    result = await service.build_daily_report(
        user_id=user_id,
        report_date=date(2026, 5, 1),
        user_timezone=ZoneInfo("UTC"),
    )

    assert result.metrics.plan_progress is not None
    assert result.metrics.plan_progress.total_stages == 2
    assert result.metrics.plan_progress.completed_stages == 1
    assert result.metrics.plan_progress.progress_percent == 50
    assert result.metrics.plan_progress.current_stage_title == "Analytics"
