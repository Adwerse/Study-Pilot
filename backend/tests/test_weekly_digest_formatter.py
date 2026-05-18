from datetime import date, datetime, timezone

from app.schemas.analytics import (
    AnalyticsDataQuality,
    AnalyticsMetrics,
    TopicFocusMetric,
)
from app.schemas.weekly_digest import DigestPeriod, WeeklyDigestReport
from app.services.weekly_digest_formatter import MAX_DIGEST_CHARS, WeeklyDigestFormatter


def make_report(
    *,
    metrics: AnalyticsMetrics | None = None,
    data_quality: AnalyticsDataQuality = AnalyticsDataQuality.medium,
    summary: str = "Ты хорошо держал фокус утром.",
    recommendations: list[str] | None = None,
) -> WeeklyDigestReport:
    return WeeklyDigestReport(
        period=DigestPeriod(
            week_start=datetime(2026, 4, 27, tzinfo=timezone.utc),
            week_end=datetime(2026, 5, 4, tzinfo=timezone.utc),
            week_start_date=date(2026, 4, 27),
            timezone="UTC",
        ),
        metrics=metrics
        or AnalyticsMetrics(
            total_focus_minutes=420,
            sessions_count=18,
            cancelled_sessions_count=3,
            completion_rate=86,
            streak_days=5,
            best_focus_hours=["09:00", "11:00"],
            most_focused_topics=[
                TopicFocusMetric(topic="RAG", minutes=160),
                TopicFocusMetric(topic="PostgreSQL", minutes=90),
            ],
        ),
        data_quality=data_quality,
        summary=summary,
        recommendations=recommendations
        if recommendations is not None
        else ["Планируй сложные задачи утром.", "Дроби крупные этапы."],
    )


def test_formatter_includes_required_digest_metrics() -> None:
    text = WeeklyDigestFormatter().format(make_report())

    assert "Фокус: 7ч 00м" in text
    assert "Сессии: 18" in text
    assert "Completion rate: 86%" in text
    assert "Streak: 5 дней" in text
    assert "Лучшие часы: 09:00, 11:00" in text
    assert "• RAG — 2ч 40м" in text
    assert "1. Планируй сложные задачи утром." in text
    assert "{" not in text


def test_formatter_omits_empty_optional_sections() -> None:
    text = WeeklyDigestFormatter().format(
        make_report(
            metrics=AnalyticsMetrics(
                total_focus_minutes=25,
                sessions_count=1,
                completion_rate=100,
                streak_days=1,
            ),
            recommendations=[],
        )
    )

    assert "Лучшие часы:" not in text
    assert "Темы недели:" not in text
    assert "Рекомендации:" not in text


def test_formatter_mentions_low_data_quality_and_trims_long_text() -> None:
    text = WeeklyDigestFormatter().format(
        make_report(
            data_quality=AnalyticsDataQuality.low,
            summary="Очень длинный итог. " * 300,
            recommendations=["Очень длинная рекомендация. " * 100],
        )
    )

    assert "выводы предварительные" in text
    assert len(text) <= MAX_DIGEST_CHARS
