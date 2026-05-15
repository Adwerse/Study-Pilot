from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from app.models.focus_log import FocusLog
from app.models.plan import Plan, PlanStage
from app.schemas.analytics import AnalyticsMetrics
from app.schemas.weekly_review import ProposedChange, WeeklyReviewMetrics


RoadmapReviewStatus = Literal["on_track", "behind", "ahead", "insufficient_data"]


@dataclass(frozen=True)
class ReviewPeriod:
    start: datetime
    end: datetime
    timezone: str


@dataclass(frozen=True)
class PlannedProgress:
    planned_stages_count: int
    planned_focus_minutes: int | None


@dataclass(frozen=True)
class ActualProgress:
    actual_focus_minutes: int
    completion_rate: int | None
    completed_stages_count: int
    total_stages_count: int
    roadmap_progress_percent: int


@dataclass(frozen=True)
class RoadmapProgressAnalysis:
    status: RoadmapReviewStatus
    metrics: WeeklyReviewMetrics
    delayed_stage_ids: list[str]
    proposed_changes: list[ProposedChange]


class RoadmapProgressAnalyzer:
    def calculate_planned_progress(
        self,
        plan: Plan,
        stages: list[PlanStage],
        period: ReviewPeriod,
        focus_sessions: list[FocusLog] | None = None,
    ) -> PlannedProgress:
        planned_stages = [
            stage
            for stage in stages
            if self._stage_is_planned_for_period(plan, stage, period)
        ]
        stage_minutes = self._planned_minutes_from_stages(planned_stages)
        focus_minutes = self._planned_minutes_from_focus(focus_sessions or [])
        return PlannedProgress(
            planned_stages_count=len(planned_stages),
            planned_focus_minutes=stage_minutes
            if stage_minutes is not None
            else focus_minutes,
        )

    def calculate_actual_progress(
        self,
        stages: list[PlanStage],
        period: ReviewPeriod,
        focus_sessions: list[FocusLog],
        weekly_metrics: AnalyticsMetrics | None,
    ) -> ActualProgress:
        actual_focus_minutes = sum(
            self._focus_minutes(session)
            for session in focus_sessions
            if session.status == "completed"
        )
        completed_stages_count = sum(
            1
            for stage in stages
            if self._stage_completed_by_period_end(stage=stage, period=period)
        )
        total_stages_count = len(stages)
        roadmap_progress_percent = (
            round((completed_stages_count / total_stages_count) * 100)
            if total_stages_count
            else 0
        )

        _ = weekly_metrics
        completed_sessions = sum(
            1 for session in focus_sessions if session.status == "completed"
        )
        cancelled_sessions = sum(
            1 for session in focus_sessions if session.status == "cancelled"
        )
        denominator = completed_sessions + cancelled_sessions
        completion_rate = (
            round((completed_sessions / denominator) * 100) if denominator else None
        )

        return ActualProgress(
            actual_focus_minutes=actual_focus_minutes,
            completion_rate=completion_rate,
            completed_stages_count=completed_stages_count,
            total_stages_count=total_stages_count,
            roadmap_progress_percent=roadmap_progress_percent,
        )

    def detect_delays(
        self,
        plan: Plan,
        stages: list[PlanStage],
        period: ReviewPeriod,
    ) -> list[PlanStage]:
        period_end_date = period.end.date()
        return [
            stage
            for stage in stages
            if not self._stage_completed_by_period_end(stage=stage, period=period)
            and self._stage_end_date(plan, stage) < period_end_date
        ]

    def build_safe_proposed_changes(
        self,
        plan: Plan,
        delayed_stages: list[PlanStage],
    ) -> list[ProposedChange]:
        changes: list[ProposedChange] = []
        for stage in delayed_stages[:3]:
            old_start = self._stage_start_date(plan, stage)
            old_end = self._stage_end_date(plan, stage)
            changes.append(
                ProposedChange(
                    type="reschedule_stage",
                    stage_id=stage.id,
                    reason="Stage was not completed by the end of the reviewed period.",
                    old_start_date=old_start,
                    old_end_date=old_end,
                    new_start_date=old_start + timedelta(days=7),
                    new_end_date=old_end + timedelta(days=7),
                )
            )
        return changes

    def analyze(
        self,
        *,
        plan: Plan,
        stages: list[PlanStage],
        period: ReviewPeriod,
        focus_sessions: list[FocusLog],
        weekly_metrics: AnalyticsMetrics | None,
    ) -> RoadmapProgressAnalysis:
        ordered_stages = sorted(stages, key=lambda stage: stage.order_index)
        planned = self.calculate_planned_progress(
            plan=plan,
            stages=ordered_stages,
            period=period,
            focus_sessions=focus_sessions,
        )
        actual = self.calculate_actual_progress(
            stages=ordered_stages,
            period=period,
            focus_sessions=focus_sessions,
            weekly_metrics=weekly_metrics,
        )
        status = self._detect_status(
            planned=planned,
            actual=actual,
            stages=ordered_stages,
            focus_sessions=focus_sessions,
        )
        delayed_stages = self.detect_delays(plan, ordered_stages, period)
        proposed_changes = (
            self.build_safe_proposed_changes(plan, delayed_stages)
            if status == "behind"
            else []
        )

        return RoadmapProgressAnalysis(
            status=status,
            metrics=WeeklyReviewMetrics(
                planned_focus_minutes=planned.planned_focus_minutes,
                actual_focus_minutes=actual.actual_focus_minutes,
                completion_rate=actual.completion_rate,
                completed_stages_count=actual.completed_stages_count,
                planned_stages_count=planned.planned_stages_count,
                total_stages_count=actual.total_stages_count,
                roadmap_progress_percent=actual.roadmap_progress_percent,
            ),
            delayed_stage_ids=[str(stage.id) for stage in delayed_stages],
            proposed_changes=proposed_changes,
        )

    def _detect_status(
        self,
        *,
        planned: PlannedProgress,
        actual: ActualProgress,
        stages: list[PlanStage],
        focus_sessions: list[FocusLog],
    ) -> RoadmapReviewStatus:
        if not stages and not focus_sessions:
            return "insufficient_data"

        if planned.planned_stages_count > actual.completed_stages_count:
            return "behind"
        if actual.completed_stages_count > planned.planned_stages_count:
            return "ahead"

        if planned.planned_focus_minutes is not None:
            if actual.actual_focus_minutes < planned.planned_focus_minutes * 0.7:
                return "behind"
            if actual.actual_focus_minutes > planned.planned_focus_minutes * 1.2:
                return "ahead"

        _ = stages
        return "on_track"

    def _stage_is_planned_for_period(
        self,
        plan: Plan,
        stage: PlanStage,
        period: ReviewPeriod,
    ) -> bool:
        stage_start = self._stage_start_date(plan, stage)
        stage_end = self._stage_end_date(plan, stage)
        period_start = period.start.date()
        period_end_exclusive = period.end.date()
        return stage_start < period_end_exclusive and stage_end >= period_start

    def _stage_start_date(self, plan: Plan, stage: PlanStage) -> date:
        if stage.start_date is not None:
            return stage.start_date
        return self._derived_stage_start_date(plan, stage)

    def _stage_end_date(self, plan: Plan, stage: PlanStage) -> date:
        if stage.end_date is not None:
            return stage.end_date
        return self._stage_start_date(plan, stage) + timedelta(days=6)

    def _stage_completed_by_period_end(
        self,
        *,
        stage: PlanStage,
        period: ReviewPeriod,
    ) -> bool:
        if stage.status != "done":
            return False

        completed_at = getattr(stage, "completed_at", None)
        period_end = self._as_aware_utc(period.end)
        if completed_at is not None:
            return self._as_aware_utc(completed_at) <= period_end

        # Legacy rows have no completion timestamp. Count them only for the
        # current/future review window, where the current status is still a
        # reasonable approximation.
        return period_end > datetime.now(timezone.utc)

    @staticmethod
    def _derived_stage_start_date(plan: Plan, stage: PlanStage) -> date:
        generated_at = plan.generated_at
        if generated_at is None:
            base_date = datetime.utcnow().date()
        else:
            base_date = generated_at.date()
        return base_date + timedelta(days=(max(stage.week_number, 1) - 1) * 7)

    @staticmethod
    def _planned_minutes_from_focus(
        focus_sessions: list[FocusLog],
    ) -> int | None:
        minutes = [
            int(session.planned_duration_minutes)
            for session in focus_sessions
            if session.planned_duration_minutes is not None
        ]
        return sum(minutes) if minutes else None

    @staticmethod
    def _planned_minutes_from_stages(stages: list[PlanStage]) -> int | None:
        minutes: list[int] = []
        for stage in stages:
            expected_hours = getattr(stage, "expected_hours", None)
            if expected_hours is not None:
                minutes.append(round(float(expected_hours) * 60))
                continue

            duration_minutes = getattr(stage, "duration_minutes", None)
            if duration_minutes is not None:
                minutes.append(int(duration_minutes))
                continue

            duration = getattr(stage, "duration", None)
            if duration is not None and isinstance(duration, (int, float)):
                minutes.append(int(duration))

        return sum(minutes) if minutes else None

    @staticmethod
    def _focus_minutes(session: FocusLog) -> int:
        return max(0, int(session.actual_duration_seconds or 0)) // 60

    @staticmethod
    def _as_aware_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
