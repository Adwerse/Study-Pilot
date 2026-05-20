from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.api.dependencies import get_current_user
from app.database import get_db
from app.schemas.analytics import (
    AnalyticsDataQuality,
    AnalyticsMetrics,
    AnalyticsNarrative,
    AnalyticsPeriod,
    AnalyticsPeriodType,
    DailyBreakdownItem,
)
from app.services.analytics_metrics_service import AnalyticsMetricsResult


def make_result(
    period_type: AnalyticsPeriodType = AnalyticsPeriodType.daily,
    daily_breakdown: list[DailyBreakdownItem] | None = None,
) -> AnalyticsMetricsResult:
    return AnalyticsMetricsResult(
        period=AnalyticsPeriod(
            type=period_type,
            start=datetime(2026, 5, 1, tzinfo=timezone.utc),
            end=datetime(2026, 5, 2, tzinfo=timezone.utc),
            timezone="UTC",
        ),
        metrics=AnalyticsMetrics(
            total_focus_seconds=1500,
            total_focus_minutes=25,
            sessions_count=1,
            cancelled_sessions_count=0,
            completion_rate=100,
            average_session_minutes=25,
            streak_days=3,
            best_focus_hours=["10:00"],
        ),
        data_quality=AnalyticsDataQuality.low,
        daily_breakdown=daily_breakdown,
    )


class FakeMetricsService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def build_daily_report(self, user_id, report_date, user_timezone):
        assert user_id == self.user_id
        _ = (report_date, user_timezone)
        return make_result()

    async def build_weekly_report(self, user_id, week_start, user_timezone):
        assert user_id == self.user_id
        _ = (week_start, user_timezone)
        breakdown = [
            DailyBreakdownItem(
                date=date(2026, 4, 27),
                focus_minutes=25,
                sessions_count=1,
                completion_rate=100,
            ),
            *[
                DailyBreakdownItem(
                    date=date(2026, 4, 28) + timedelta(days=offset),
                    focus_minutes=0,
                    sessions_count=0,
                    completion_rate=0,
                )
                for offset in range(6)
            ],
        ]
        return make_result(
            period_type=AnalyticsPeriodType.weekly,
            daily_breakdown=breakdown,
        )


@pytest.fixture
def analytics_overrides(app, monkeypatch):
    user_id = uuid4()

    async def fake_current_user() -> dict:
        return {"id": 123, "username": "tester"}

    async def fake_db():
        yield object()

    async def fake_resolve_user_id(current_user, db) -> UUID:
        _ = (current_user, db)
        return user_id

    async def fake_generate_report(**kwargs):
        _ = kwargs
        return AnalyticsNarrative(
            summary="Test report.",
            recommendations=["Do one focus block."],
        )

    from app.api import analytics as analytics_api

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(analytics_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(
        analytics_api,
        "build_metrics_service",
        lambda db: FakeMetricsService(user_id),
    )
    monkeypatch.setattr(
        analytics_api.analytics_agent,
        "generate_report",
        fake_generate_report,
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_daily_report_endpoint_returns_full_report(client, analytics_overrides):
    _ = analytics_overrides
    response = await client.get("/api/v1/analytics/daily?date=2026-05-01")

    assert response.status_code == 200
    payload = response.json()
    assert payload["period"]["type"] == "daily"
    assert payload["metrics"]["total_focus_minutes"] == 25
    assert payload["summary"] == "Test report."
    assert payload["data_quality"] == "low"


@pytest.mark.asyncio
async def test_weekly_report_endpoint_returns_breakdown(client, analytics_overrides):
    _ = analytics_overrides
    response = await client.get("/api/v1/analytics/weekly?week_start=2026-04-29")

    assert response.status_code == 200
    payload = response.json()
    assert payload["period"]["type"] == "weekly"
    assert len(payload["daily_breakdown"]) == 7
    assert payload["daily_breakdown"][0]["focus_minutes"] == 25


@pytest.mark.asyncio
async def test_legacy_today_week_and_streak_endpoints(client, analytics_overrides):
    _ = analytics_overrides

    today = await client.get("/api/v1/analytics/today?date=2026-05-01")
    week = await client.get("/api/v1/analytics/week?week_start=2026-04-29")
    streak = await client.get("/api/v1/analytics/streak")

    assert today.status_code == 200
    assert today.json()["total_minutes"] == 25
    assert today.json()["best_hour"] == 10
    assert week.status_code == 200
    assert len(week.json()) == 7
    assert streak.status_code == 200
    assert streak.json() == {"streak_days": 3}


@pytest.mark.asyncio
async def test_invalid_timezone_returns_422(client, analytics_overrides):
    _ = analytics_overrides
    response = await client.get("/api/v1/analytics/daily?timezone=Not/AZone")

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid timezone"


@pytest.mark.asyncio
async def test_no_data_returns_valid_empty_report(app, client, monkeypatch):
    user_id = uuid4()

    async def fake_current_user() -> dict:
        return {"id": 123, "username": "tester"}

    async def fake_db():
        yield object()

    async def fake_resolve_user_id(current_user, db) -> UUID:
        _ = (current_user, db)
        return user_id

    class EmptyMetricsService:
        async def build_daily_report(self, user_id, report_date, user_timezone):
            _ = (user_id, report_date, user_timezone)
            return AnalyticsMetricsResult(
                period=AnalyticsPeriod(
                    type=AnalyticsPeriodType.daily,
                    start=datetime(2026, 5, 1, tzinfo=timezone.utc),
                    end=datetime(2026, 5, 2, tzinfo=timezone.utc),
                    timezone="UTC",
                ),
                metrics=AnalyticsMetrics(),
                data_quality=AnalyticsDataQuality.low,
            )

    async def fake_generate_report(**kwargs):
        _ = kwargs
        return AnalyticsNarrative(
            summary="Data is still limited.",
            recommendations=["Start with one short 15-25 minute block."],
        )

    from app.api import analytics as analytics_api

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(analytics_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(
        analytics_api,
        "build_metrics_service",
        lambda db: EmptyMetricsService(),
    )
    monkeypatch.setattr(
        analytics_api.analytics_agent,
        "generate_report",
        fake_generate_report,
    )
    try:
        response = await client.get("/api/v1/analytics/daily?date=2026-05-01")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["metrics"]["total_focus_minutes"] == 0
    assert payload["metrics"]["sessions_count"] == 0
    assert payload["data_quality"] == "low"
