from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.schemas.analytics import (
    AnalyticsDataQuality,
    AnalyticsMetrics,
    AnalyticsPeriod,
    AnalyticsPeriodType,
    TopicFocusMetric,
)
from app.services.analytics_agent import AnalyticsAgent


def make_period() -> AnalyticsPeriod:
    return AnalyticsPeriod(
        type=AnalyticsPeriodType.daily,
        start=datetime(2026, 5, 1, tzinfo=timezone.utc),
        end=datetime(2026, 5, 2, tzinfo=timezone.utc),
        timezone="UTC",
    )


@pytest.mark.asyncio
async def test_generate_report_maps_valid_llm_json(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ANALYTICS_AI_ENABLED", True)
    monkeypatch.setattr(settings, "TENSORIX_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.analytics_agent.complete",
        AsyncMock(
            return_value='{"summary":"Короткий честный отчёт.","recommendations":["Сделай один блок."]}'
        ),
    )

    narrative = await AnalyticsAgent().generate_report(
        period=make_period(),
        metrics=AnalyticsMetrics(total_focus_minutes=25, sessions_count=1),
        data_quality=AnalyticsDataQuality.low,
    )

    assert narrative.summary == "Короткий честный отчёт."
    assert narrative.recommendations == ["Сделай один блок."]


@pytest.mark.asyncio
async def test_llm_failure_uses_fallback_summary(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ANALYTICS_AI_ENABLED", True)
    monkeypatch.setattr(settings, "TENSORIX_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.analytics_agent.complete",
        AsyncMock(side_effect=RuntimeError("provider down")),
    )

    narrative = await AnalyticsAgent().generate_report(
        period=make_period(),
        metrics=AnalyticsMetrics(total_focus_minutes=0, sessions_count=0),
        data_quality=AnalyticsDataQuality.low,
    )

    assert "нет завершённых" in narrative.summary
    assert narrative.recommendations


def test_low_data_quality_fallback_is_cautious() -> None:
    narrative = AnalyticsAgent().generate_fallback_report(
        period=make_period(),
        metrics=AnalyticsMetrics(
            total_focus_minutes=25,
            sessions_count=1,
            most_focused_topics=[TopicFocusMetric(topic="FastAPI", minutes=25)],
        ),
        data_quality=AnalyticsDataQuality.low,
    )

    assert "Данных пока мало" in narrative.summary
    assert "100%" not in narrative.summary


def test_no_data_fallback_does_not_invent_activity() -> None:
    narrative = AnalyticsAgent().generate_fallback_report(
        period=make_period(),
        metrics=AnalyticsMetrics(),
        data_quality=AnalyticsDataQuality.low,
    )

    assert "нет завершённых" in narrative.summary
    assert "95" not in narrative.summary
    assert narrative.recommendations == [
        "Начни с одного короткого блока на 15-25 минут."
    ]
