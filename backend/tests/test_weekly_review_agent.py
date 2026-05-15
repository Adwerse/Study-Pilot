from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.config import settings
from app.models.focus_log import FocusLog
from app.models.plan import Plan, PlanStage
from app.schemas.analytics import AnalyticsMetrics
from app.services.roadmap_progress_analyzer import ReviewPeriod, RoadmapProgressAnalyzer
from app.services.weekly_review_agent import WeeklyReviewAgent


UTC = timezone.utc


def make_plan() -> Plan:
    stage = PlanStage(
        id=uuid4(),
        plan_id=uuid4(),
        week_number=1,
        title="RAG API",
        deliverable="Working API",
        status="in_progress",
        order_index=0,
        start_date=datetime(2026, 4, 27, tzinfo=UTC).date(),
        end_date=datetime(2026, 5, 3, tzinfo=UTC).date(),
    )
    plan = Plan(
        id=stage.plan_id,
        user_id=uuid4(),
        title="RAG Plan",
        status="active",
        generated_at=datetime(2026, 4, 27, tzinfo=UTC),
    )
    plan.stages = [stage]
    return plan


def make_period() -> ReviewPeriod:
    return ReviewPeriod(
        start=datetime(2026, 4, 27, tzinfo=UTC),
        end=datetime(2026, 5, 4, tzinfo=UTC),
        timezone="UTC",
    )


def make_focus(status: str = "completed") -> FocusLog:
    return FocusLog(
        id=uuid4(),
        user_id=uuid4(),
        status=status,
        started_at=datetime(2026, 4, 28, 10, tzinfo=UTC),
        actual_duration_seconds=1500,
        planned_duration_minutes=25,
    )


@pytest.mark.asyncio
async def test_generates_fallback_review_when_llm_fails(monkeypatch) -> None:
    monkeypatch.setattr(settings, "WEEKLY_REVIEW_AI_ENABLED", True)
    monkeypatch.setattr(settings, "TENSORIX_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.weekly_review_agent.complete",
        AsyncMock(side_effect=RuntimeError("provider down")),
    )
    plan = make_plan()
    period = make_period()
    analysis = RoadmapProgressAnalyzer().analyze(
        plan=plan,
        stages=plan.stages,
        period=period,
        focus_sessions=[make_focus("cancelled")],
        weekly_metrics=AnalyticsMetrics(cancelled_sessions_count=1),
    )

    result = await WeeklyReviewAgent().generate_review(
        user_id=plan.user_id,
        plan=plan,
        stages=plan.stages,
        weekly_metrics=AnalyticsMetrics(cancelled_sessions_count=1),
        focus_sessions=[make_focus("cancelled")],
        timezone="UTC",
        period=period,
        deterministic_analysis=analysis,
    )

    assert result.summary
    assert result.metrics == analysis.metrics
    assert result.proposed_changes


@pytest.mark.asyncio
async def test_invalid_llm_json_uses_fallback(monkeypatch) -> None:
    monkeypatch.setattr(settings, "WEEKLY_REVIEW_AI_ENABLED", True)
    monkeypatch.setattr(settings, "TENSORIX_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.weekly_review_agent.complete",
        AsyncMock(return_value="not-json"),
    )
    plan = make_plan()
    plan.stages = []
    period = make_period()

    result = await WeeklyReviewAgent().generate_review(
        user_id=plan.user_id,
        plan=plan,
        stages=plan.stages,
        weekly_metrics=AnalyticsMetrics(),
        focus_sessions=[],
        timezone="UTC",
        period=period,
    )

    assert result.analysis_status == "insufficient_data"
    assert result.recommendations
    assert "data" in result.summary.lower()


def test_validates_llm_proposed_changes_stage_id() -> None:
    plan = make_plan()
    stage_id = plan.stages[0].id
    changes = WeeklyReviewAgent().validate_proposed_changes(
        [
            {
                "type": "reschedule_stage",
                "stage_id": str(stage_id),
                "reason": "Delayed",
                "old_start_date": "2026-04-27",
                "old_end_date": "2026-05-03",
                "new_start_date": "2026-05-04",
                "new_end_date": "2026-05-10",
            },
            {
                "type": "reschedule_stage",
                "stage_id": str(uuid4()),
                "reason": "Foreign",
                "old_start_date": "2026-04-27",
                "old_end_date": "2026-05-03",
                "new_start_date": "2026-05-04",
                "new_end_date": "2026-05-10",
            },
        ],
        stages=plan.stages,
    )

    assert len(changes) == 1
    assert changes[0].stage_id == stage_id


def test_drops_unsafe_change_types() -> None:
    plan = make_plan()

    changes = WeeklyReviewAgent().validate_proposed_changes(
        [
            {
                "type": "delete_stage",
                "stage_id": str(plan.stages[0].id),
                "reason": "Bad",
            }
        ],
        stages=plan.stages,
    )

    assert changes == []


def test_drops_invalid_date_ranges() -> None:
    plan = make_plan()

    changes = WeeklyReviewAgent().validate_proposed_changes(
        [
            {
                "type": "reschedule_stage",
                "stage_id": str(plan.stages[0].id),
                "reason": "Bad dates",
                "old_start_date": "2026-05-03",
                "old_end_date": "2026-04-27",
                "new_start_date": "2026-05-04",
                "new_end_date": "2026-05-10",
            }
        ],
        stages=plan.stages,
    )

    assert changes == []


@pytest.mark.asyncio
async def test_llm_cannot_invent_metrics(monkeypatch) -> None:
    monkeypatch.setattr(settings, "WEEKLY_REVIEW_AI_ENABLED", True)
    monkeypatch.setattr(settings, "TENSORIX_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.weekly_review_agent.complete",
        AsyncMock(
            return_value=(
                '{"summary":"ok","insights":["fake 999 minutes"],'
                '"risks":[],"recommendations":[],"metrics":{"actual_focus_minutes":999},'
                '"proposed_changes":[]}'
            )
        ),
    )
    plan = make_plan()
    period = make_period()
    focus = [make_focus("completed")]

    result = await WeeklyReviewAgent().generate_review(
        user_id=plan.user_id,
        plan=plan,
        stages=plan.stages,
        weekly_metrics=AnalyticsMetrics(total_focus_minutes=25, sessions_count=1),
        focus_sessions=focus,
        timezone="UTC",
        period=period,
    )

    assert result.metrics.actual_focus_minutes == 25
    assert result.metrics.actual_focus_minutes != 999


@pytest.mark.asyncio
async def test_insufficient_data_status_and_recommendation() -> None:
    plan = make_plan()
    plan.stages = []
    result = await WeeklyReviewAgent().generate_review(
        user_id=plan.user_id,
        plan=plan,
        stages=plan.stages,
        weekly_metrics=AnalyticsMetrics(),
        focus_sessions=[],
        timezone="UTC",
        period=make_period(),
    )

    assert result.analysis_status == "insufficient_data"
    assert any("focus" in item.lower() for item in result.recommendations)
