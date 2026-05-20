from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from app.models.focus_log import FocusLog
from app.models.plan import PlanStage
from app.repositories.focus_repository import FocusRepository
from app.repositories.plan_repository import PlanRepository
from app.schemas.analytics import (
    AnalyticsDataQuality,
    AnalyticsMetrics,
    AnalyticsPeriod,
    AnalyticsPeriodType,
    DailyBreakdownItem,
    PlanProgressMetric,
    TopicFocusMetric,
)


UNTITLED_TOPIC = "Untitled topic"


@dataclass(frozen=True)
class AnalyticsMetricsResult:
    period: AnalyticsPeriod
    metrics: AnalyticsMetrics
    data_quality: AnalyticsDataQuality
    daily_breakdown: list[DailyBreakdownItem] | None = None


class AnalyticsMetricsService:
    def __init__(self, focus_repo: FocusRepository, plan_repo: PlanRepository):
        self.focus_repo = focus_repo
        self.plan_repo = plan_repo

    async def build_daily_report(
        self,
        user_id: UUID,
        report_date: date | None,
        user_timezone: ZoneInfo,
    ) -> AnalyticsMetricsResult:
        local_date = report_date or datetime.now(user_timezone).date()
        start_local = datetime.combine(local_date, time.min, tzinfo=user_timezone)
        end_local = start_local + timedelta(days=1)
        return await self._build_report(
            user_id=user_id,
            period_type=AnalyticsPeriodType.daily,
            start_local=start_local,
            end_local=end_local,
            streak_anchor_date=local_date,
            user_timezone=user_timezone,
            include_daily_breakdown=False,
        )

    async def build_weekly_report(
        self,
        user_id: UUID,
        week_start: date | None,
        user_timezone: ZoneInfo,
    ) -> AnalyticsMetricsResult:
        selected_date = week_start or datetime.now(user_timezone).date()
        monday = selected_date - timedelta(days=selected_date.weekday())
        start_local = datetime.combine(monday, time.min, tzinfo=user_timezone)
        end_local = start_local + timedelta(days=7)
        return await self._build_report(
            user_id=user_id,
            period_type=AnalyticsPeriodType.weekly,
            start_local=start_local,
            end_local=end_local,
            streak_anchor_date=end_local.date() - timedelta(days=1),
            user_timezone=user_timezone,
            include_daily_breakdown=True,
        )

    async def _build_report(
        self,
        user_id: UUID,
        period_type: AnalyticsPeriodType,
        start_local: datetime,
        end_local: datetime,
        streak_anchor_date: date,
        user_timezone: ZoneInfo,
        include_daily_breakdown: bool,
    ) -> AnalyticsMetricsResult:
        start_utc = start_local.astimezone(timezone.utc)
        end_utc = end_local.astimezone(timezone.utc)
        sessions = await self.focus_repo.list_sessions_between(
            user_id=user_id,
            start_utc=start_utc,
            end_utc=end_utc,
            statuses=("completed", "cancelled"),
        )
        streak_days = await self._calculate_streak_days(
            user_id=user_id,
            anchor_date=streak_anchor_date,
            user_timezone=user_timezone,
        )
        plan_progress = await self._get_plan_progress(user_id)
        metrics = self._calculate_metrics(
            sessions=sessions,
            streak_days=streak_days,
            plan_progress=plan_progress,
            user_timezone=user_timezone,
        )
        data_quality = self._calculate_data_quality(period_type, metrics.sessions_count)
        daily_breakdown = (
            self._calculate_daily_breakdown(
                sessions=sessions,
                start_date=start_local.date(),
                days=(end_local.date() - start_local.date()).days,
                user_timezone=user_timezone,
            )
            if include_daily_breakdown
            else None
        )
        return AnalyticsMetricsResult(
            period=AnalyticsPeriod(
                type=period_type,
                start=start_utc,
                end=end_utc,
                timezone=user_timezone.key,
            ),
            metrics=metrics,
            data_quality=data_quality,
            daily_breakdown=daily_breakdown,
        )

    def _calculate_metrics(
        self,
        sessions: list[FocusLog],
        streak_days: int,
        plan_progress: PlanProgressMetric | None,
        user_timezone: ZoneInfo,
    ) -> AnalyticsMetrics:
        completed = [session for session in sessions if session.status == "completed"]
        cancelled_count = sum(
            1 for session in sessions if session.status == "cancelled"
        )
        total_focus_seconds = sum(
            self._duration_seconds(session) for session in completed
        )
        total_focus_minutes = total_focus_seconds // 60
        sessions_count = len(completed)
        completion_rate = self._completion_rate(sessions_count, cancelled_count)
        average_session_minutes = (
            round(total_focus_minutes / sessions_count) if sessions_count else None
        )

        return AnalyticsMetrics(
            total_focus_seconds=total_focus_seconds,
            total_focus_minutes=total_focus_minutes,
            sessions_count=sessions_count,
            cancelled_sessions_count=cancelled_count,
            completion_rate=completion_rate,
            average_session_minutes=average_session_minutes,
            streak_days=streak_days,
            best_focus_hours=self._best_focus_hours(completed, user_timezone),
            most_focused_topics=self._most_focused_topics(completed),
            plan_progress=plan_progress,
        )

    async def _calculate_streak_days(
        self,
        user_id: UUID,
        anchor_date: date,
        user_timezone: ZoneInfo,
    ) -> int:
        anchor_end_local = datetime.combine(
            anchor_date + timedelta(days=1),
            time.min,
            tzinfo=user_timezone,
        )
        sessions = await self.focus_repo.list_completed_sessions_until(
            user_id=user_id,
            end_utc=anchor_end_local.astimezone(timezone.utc),
        )
        active_days = {
            self._as_local(session.started_at, user_timezone).date()
            for session in sessions
            if self._duration_seconds(session) > 0
        }

        streak_days = 0
        current_date = anchor_date
        while current_date in active_days:
            streak_days += 1
            current_date -= timedelta(days=1)
        return streak_days

    async def _get_plan_progress(self, user_id: UUID) -> PlanProgressMetric | None:
        plan = await self.plan_repo.get_active_by_user(user_id)
        if plan is None:
            return None

        stages = sorted(
            list(getattr(plan, "stages", []) or []),
            key=lambda stage: stage.order_index,
        )
        total_stages = len(stages)
        completed_stages = sum(1 for stage in stages if stage.status == "done")
        current_stage = self._current_stage(stages)
        progress_percent = (
            round((completed_stages / total_stages) * 100) if total_stages else 0
        )

        return PlanProgressMetric(
            plan_id=plan.id,
            title=plan.title,
            total_stages=total_stages,
            completed_stages=completed_stages,
            progress_percent=progress_percent,
            current_stage_id=current_stage.id if current_stage else None,
            current_stage_title=current_stage.title if current_stage else None,
        )

    def _calculate_daily_breakdown(
        self,
        sessions: list[FocusLog],
        start_date: date,
        days: int,
        user_timezone: ZoneInfo,
    ) -> list[DailyBreakdownItem]:
        breakdown: dict[date, dict[str, int]] = {
            start_date + timedelta(days=offset): {
                "focus_seconds": 0,
                "completed": 0,
                "cancelled": 0,
            }
            for offset in range(days)
        }

        for session in sessions:
            local_date = self._as_local(session.started_at, user_timezone).date()
            if local_date not in breakdown:
                continue
            if session.status == "completed":
                breakdown[local_date]["completed"] += 1
                breakdown[local_date]["focus_seconds"] += self._duration_seconds(
                    session
                )
            elif session.status == "cancelled":
                breakdown[local_date]["cancelled"] += 1

        return [
            DailyBreakdownItem(
                date=item_date,
                focus_minutes=values["focus_seconds"] // 60,
                sessions_count=values["completed"],
                completion_rate=self._completion_rate(
                    values["completed"],
                    values["cancelled"],
                ),
            )
            for item_date, values in sorted(breakdown.items())
        ]

    def _best_focus_hours(
        self,
        completed_sessions: list[FocusLog],
        user_timezone: ZoneInfo,
    ) -> list[str]:
        by_hour: dict[int, dict[str, int]] = {}
        for session in completed_sessions:
            hour = self._as_local(session.started_at, user_timezone).hour
            bucket = by_hour.setdefault(hour, {"seconds": 0, "sessions": 0})
            bucket["seconds"] += self._duration_seconds(session)
            bucket["sessions"] += 1

        ranked_hours = sorted(
            by_hour.items(),
            key=lambda item: (
                -(item[1]["seconds"] // 60),
                -item[1]["sessions"],
                item[0],
            ),
        )
        return [f"{hour:02d}:00" for hour, _ in ranked_hours[:3]]

    def _most_focused_topics(
        self,
        completed_sessions: list[FocusLog],
    ) -> list[TopicFocusMetric]:
        by_topic: dict[str, int] = {}
        for session in completed_sessions:
            seconds = self._duration_seconds(session)
            if seconds <= 0:
                continue
            topic = session.topic.strip() if isinstance(session.topic, str) else ""
            topic = topic or UNTITLED_TOPIC
            by_topic[topic] = by_topic.get(topic, 0) + seconds

        ranked_topics = sorted(
            by_topic.items(),
            key=lambda item: (-(item[1] // 60), item[0].lower()),
        )
        return [
            TopicFocusMetric(topic=topic, minutes=seconds // 60)
            for topic, seconds in ranked_topics[:5]
            if seconds // 60 > 0
        ]

    def _calculate_data_quality(
        self,
        period_type: AnalyticsPeriodType,
        sessions_count: int,
    ) -> AnalyticsDataQuality:
        if period_type == AnalyticsPeriodType.weekly:
            if sessions_count < 5:
                return AnalyticsDataQuality.low
            if sessions_count < 15:
                return AnalyticsDataQuality.medium
            return AnalyticsDataQuality.high

        if sessions_count < 3:
            return AnalyticsDataQuality.low
        if sessions_count < 10:
            return AnalyticsDataQuality.medium
        return AnalyticsDataQuality.high

    @staticmethod
    def _completion_rate(completed_count: int, cancelled_count: int) -> int:
        denominator = completed_count + cancelled_count
        if denominator == 0:
            return 0
        return round((completed_count / denominator) * 100)

    @staticmethod
    def _duration_seconds(session: FocusLog) -> int:
        return max(0, int(session.actual_duration_seconds or 0))

    @staticmethod
    def _as_local(value: datetime, user_timezone: ZoneInfo) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(user_timezone)

    @staticmethod
    def _current_stage(stages: list[PlanStage]) -> PlanStage | None:
        for status in ("in_progress", "pending"):
            for stage in stages:
                if stage.status == status:
                    return stage
        return None


__all__ = ["AnalyticsMetricsResult", "AnalyticsMetricsService", "UNTITLED_TOPIC"]
