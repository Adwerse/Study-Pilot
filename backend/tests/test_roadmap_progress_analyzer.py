from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.focus_log import FocusLog
from app.models.plan import Plan, PlanStage
from app.schemas.analytics import AnalyticsMetrics
from app.services.roadmap_progress_analyzer import ReviewPeriod, RoadmapProgressAnalyzer


UTC = timezone.utc


def make_period() -> ReviewPeriod:
    return ReviewPeriod(
        start=datetime(2026, 4, 27, tzinfo=UTC),
        end=datetime(2026, 5, 4, tzinfo=UTC),
        timezone="UTC",
    )


def make_plan(stages: list[PlanStage]) -> Plan:
    plan = Plan(
        id=uuid4(),
        user_id=uuid4(),
        title="Backend Plan",
        status="active",
        generated_at=datetime(2026, 4, 27, tzinfo=UTC),
    )
    plan.stages = stages
    return plan


def make_stage(
    *,
    status: str,
    week_number: int = 1,
    order_index: int = 0,
    completed_at: datetime | None = None,
) -> PlanStage:
    return PlanStage(
        id=uuid4(),
        plan_id=uuid4(),
        week_number=week_number,
        title=f"Stage {order_index}",
        deliverable="Deliverable",
        status=status,
        order_index=order_index,
        completed_at=completed_at,
    )


def make_focus(status: str, seconds: int = 1500, planned: int | None = 25) -> FocusLog:
    return FocusLog(
        id=uuid4(),
        user_id=uuid4(),
        status=status,
        started_at=datetime(2026, 4, 28, 10, tzinfo=UTC),
        actual_duration_seconds=seconds,
        planned_duration_minutes=planned,
    )


def test_detects_behind_when_planned_stages_exceed_completed() -> None:
    analyzer = RoadmapProgressAnalyzer()
    plan = make_plan([make_stage(status="in_progress")])

    result = analyzer.analyze(
        plan=plan,
        stages=plan.stages,
        period=make_period(),
        focus_sessions=[make_focus("cancelled", seconds=0)],
        weekly_metrics=AnalyticsMetrics(cancelled_sessions_count=1),
    )

    assert result.status == "behind"
    assert result.metrics.planned_stages_count == 1
    assert result.metrics.completed_stages_count == 0
    assert result.proposed_changes[0].type == "reschedule_stage"


def test_detects_ahead_when_completed_exceeds_planned() -> None:
    analyzer = RoadmapProgressAnalyzer()
    plan = make_plan(
        [
            make_stage(status="done", week_number=1, order_index=0),
            make_stage(status="done", week_number=2, order_index=1),
        ]
    )
    for stage in plan.stages:
        stage.completed_at = datetime(2026, 5, 3, 12, tzinfo=UTC)

    result = analyzer.analyze(
        plan=plan,
        stages=plan.stages,
        period=make_period(),
        focus_sessions=[make_focus("completed")],
        weekly_metrics=AnalyticsMetrics(total_focus_minutes=25, sessions_count=1),
    )

    assert result.status == "ahead"
    assert result.metrics.planned_stages_count == 1
    assert result.metrics.completed_stages_count == 2


def test_handles_no_planned_focus_minutes() -> None:
    analyzer = RoadmapProgressAnalyzer()
    plan = make_plan(
        [make_stage(status="done", completed_at=datetime(2026, 5, 1, tzinfo=UTC))]
    )

    result = analyzer.analyze(
        plan=plan,
        stages=plan.stages,
        period=make_period(),
        focus_sessions=[make_focus("completed", planned=None)],
        weekly_metrics=AnalyticsMetrics(total_focus_minutes=25, sessions_count=1),
    )

    assert result.metrics.planned_focus_minutes is None


def test_handles_zero_total_stages() -> None:
    analyzer = RoadmapProgressAnalyzer()
    plan = make_plan([])

    result = analyzer.analyze(
        plan=plan,
        stages=[],
        period=make_period(),
        focus_sessions=[],
        weekly_metrics=AnalyticsMetrics(),
    )

    assert result.metrics.roadmap_progress_percent == 0
    assert result.status == "insufficient_data"


def test_calculates_roadmap_progress_percent() -> None:
    analyzer = RoadmapProgressAnalyzer()
    plan = make_plan(
        [
            make_stage(
                status="done",
                order_index=0,
                completed_at=datetime(2026, 5, 1, tzinfo=UTC),
            ),
            make_stage(status="pending", order_index=1),
        ]
    )

    result = analyzer.analyze(
        plan=plan,
        stages=plan.stages,
        period=make_period(),
        focus_sessions=[make_focus("completed")],
        weekly_metrics=AnalyticsMetrics(total_focus_minutes=25, sessions_count=1),
    )

    assert result.metrics.roadmap_progress_percent == 50


def test_actual_focus_minutes_counts_only_completed_sessions() -> None:
    analyzer = RoadmapProgressAnalyzer()
    plan = make_plan(
        [make_stage(status="done", completed_at=datetime(2026, 5, 1, tzinfo=UTC))]
    )

    result = analyzer.analyze(
        plan=plan,
        stages=plan.stages,
        period=make_period(),
        focus_sessions=[
            make_focus("completed", seconds=1500),
            make_focus("cancelled", seconds=3600),
        ],
        weekly_metrics=AnalyticsMetrics(
            total_focus_minutes=25,
            sessions_count=1,
            cancelled_sessions_count=1,
        ),
    )

    assert result.metrics.actual_focus_minutes == 25


def test_metrics_include_total_stages_count() -> None:
    analyzer = RoadmapProgressAnalyzer()
    plan = make_plan(
        [
            make_stage(status="done", completed_at=datetime(2026, 5, 1, tzinfo=UTC)),
            make_stage(status="pending", order_index=1),
        ]
    )

    result = analyzer.analyze(
        plan=plan,
        stages=plan.stages,
        period=make_period(),
        focus_sessions=[make_focus("completed")],
        weekly_metrics=AnalyticsMetrics(total_focus_minutes=25, sessions_count=1),
    )

    assert result.metrics.total_stages_count == 2


def test_completion_rate_is_none_when_no_sessions() -> None:
    analyzer = RoadmapProgressAnalyzer()
    plan = make_plan([])

    result = analyzer.analyze(
        plan=plan,
        stages=[],
        period=make_period(),
        focus_sessions=[],
        weekly_metrics=AnalyticsMetrics(),
    )

    assert result.metrics.completion_rate is None


def test_completed_after_period_end_is_not_counted() -> None:
    analyzer = RoadmapProgressAnalyzer()
    plan = make_plan(
        [
            make_stage(
                status="done",
                completed_at=datetime(2026, 5, 5, tzinfo=UTC),
            )
        ]
    )

    result = analyzer.analyze(
        plan=plan,
        stages=plan.stages,
        period=make_period(),
        focus_sessions=[make_focus("completed")],
        weekly_metrics=AnalyticsMetrics(total_focus_minutes=25, sessions_count=1),
    )

    assert result.metrics.completed_stages_count == 0
    assert result.status == "behind"


def test_legacy_completed_stage_counts_only_for_current_or_future_period() -> None:
    analyzer = RoadmapProgressAnalyzer()
    plan = make_plan([make_stage(status="done")])
    now = datetime.now(UTC)
    current_monday = now.date() - timedelta(days=now.weekday())
    current_period = ReviewPeriod(
        start=datetime.combine(current_monday, datetime.min.time(), tzinfo=UTC),
        end=datetime.combine(
            current_monday + timedelta(days=7),
            datetime.min.time(),
            tzinfo=UTC,
        ),
        timezone="UTC",
    )

    historical = analyzer.analyze(
        plan=plan,
        stages=plan.stages,
        period=make_period(),
        focus_sessions=[make_focus("completed")],
        weekly_metrics=AnalyticsMetrics(total_focus_minutes=25, sessions_count=1),
    )
    current = analyzer.analyze(
        plan=plan,
        stages=plan.stages,
        period=current_period,
        focus_sessions=[make_focus("completed")],
        weekly_metrics=AnalyticsMetrics(total_focus_minutes=25, sessions_count=1),
    )

    assert historical.metrics.completed_stages_count == 0
    assert current.metrics.completed_stages_count == 1
