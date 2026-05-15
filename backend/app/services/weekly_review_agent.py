import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from app.agents.llm_client import complete
from app.config import settings
from app.models.focus_log import FocusLog
from app.models.plan import Plan, PlanStage
from app.schemas.analytics import AnalyticsMetrics, DailyBreakdownItem
from app.schemas.weekly_review import ProposedChange, WeeklyReviewMetrics
from app.services.analytics_metrics_service import AnalyticsMetricsResult
from app.services.roadmap_progress_analyzer import (
    ReviewPeriod,
    RoadmapProgressAnalysis,
    RoadmapProgressAnalyzer,
)


logger = logging.getLogger(__name__)


WEEKLY_REVIEW_SYSTEM_PROMPT = (
    "You are the Weekly Review Agent for StudyPilot. Your job is to compare "
    "the user's learning roadmap with actual weekly progress and suggest safe "
    "roadmap improvements. Use only the provided data. Do not invent completed "
    "stages, dates, focus minutes, or progress. If data is insufficient, say "
    "that clearly. Return only valid JSON."
)

ALLOWED_CHANGE_TYPES = {
    "reschedule_stage",
    "split_stage",
    "adjust_stage_focus",
    "mark_stage_at_risk",
}


@dataclass(frozen=True)
class WeeklyReviewAgentResult:
    summary: str
    insights: list[str]
    risks: list[str]
    recommendations: list[str]
    metrics: WeeklyReviewMetrics
    proposed_changes: list[ProposedChange]
    analysis_status: str


class WeeklyReviewAgent:
    def __init__(self, analyzer: RoadmapProgressAnalyzer | None = None):
        self.analyzer = analyzer or RoadmapProgressAnalyzer()

    async def generate_review(
        self,
        user_id: UUID,
        plan: Plan,
        stages: list[PlanStage],
        weekly_metrics: AnalyticsMetricsResult | AnalyticsMetrics,
        focus_sessions: list[FocusLog],
        timezone: str | ZoneInfo,
        period: ReviewPeriod | None = None,
        deterministic_analysis: RoadmapProgressAnalysis | None = None,
        daily_breakdown: list[DailyBreakdownItem] | None = None,
    ) -> WeeklyReviewAgentResult:
        timezone_name = (
            timezone.key if isinstance(timezone, ZoneInfo) else str(timezone)
        )
        period = period or self._period_from_metrics(weekly_metrics, timezone_name)
        analytics_metrics = self._metrics_from_weekly_metrics(weekly_metrics)
        daily_breakdown = daily_breakdown or self._daily_breakdown_from_metrics(
            weekly_metrics
        )

        analysis = deterministic_analysis or self.analyzer.analyze(
            plan=plan,
            stages=stages,
            period=period,
            focus_sessions=focus_sessions,
            weekly_metrics=analytics_metrics,
        )
        fallback = self.generate_fallback_review(
            plan=plan,
            stages=stages,
            analysis=analysis,
            focus_sessions=focus_sessions,
            weekly_metrics=analytics_metrics,
        )

        if not settings.WEEKLY_REVIEW_AI_ENABLED or not settings.TENSORIX_API_KEY:
            return fallback

        try:
            raw = await complete(
                messages=[
                    {"role": "system", "content": WEEKLY_REVIEW_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": self._build_user_payload(
                            plan=plan,
                            stages=stages,
                            metrics=analytics_metrics,
                            daily_breakdown=daily_breakdown,
                            focus_sessions=focus_sessions,
                            analysis=analysis,
                        ),
                    },
                ],
                model=(
                    settings.WEEKLY_REVIEW_MODEL
                    or settings.ANALYTICS_MODEL
                    or settings.TENSORIX_MODEL
                ),
                temperature=0.3,
                max_tokens=1200,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(raw)
            proposed_changes = self.validate_proposed_changes(
                parsed.get("proposed_changes", []),
                stages=stages,
            )
            return WeeklyReviewAgentResult(
                summary=self._clean_text(parsed.get("summary")) or fallback.summary,
                insights=(
                    self._clean_text_list(parsed.get("insights"))[:5]
                    or fallback.insights
                ),
                risks=self._clean_text_list(parsed.get("risks"))[:5] or fallback.risks,
                recommendations=(
                    self._clean_text_list(parsed.get("recommendations"))[:5]
                    or fallback.recommendations
                ),
                metrics=analysis.metrics,
                proposed_changes=proposed_changes or fallback.proposed_changes,
                analysis_status=analysis.status,
            )
        except Exception:
            logger.exception("Weekly review LLM generation failed")
            return fallback

    def generate_fallback_review(
        self,
        *,
        plan: Plan,
        stages: list[PlanStage],
        analysis: RoadmapProgressAnalysis,
        focus_sessions: list[FocusLog],
        weekly_metrics: AnalyticsMetrics | None,
    ) -> WeeklyReviewAgentResult:
        _ = plan
        metrics = analysis.metrics
        if analysis.status == "insufficient_data":
            summary = (
                "There is not enough roadmap or focus data for a confident weekly "
                "review yet."
            )
        elif analysis.status == "behind":
            summary = (
                "The roadmap is behind the expected pace for this week based on "
                "stage completion and focus activity."
            )
        elif analysis.status == "ahead":
            summary = (
                "The roadmap is ahead of the expected pace for this week based on "
                "completed stages or focus activity."
            )
        else:
            summary = (
                "The roadmap is broadly on track for this week based on the "
                "available progress and focus data."
            )

        insights = self._fallback_insights(
            metrics=metrics,
            stages=stages,
            weekly_metrics=weekly_metrics,
        )
        risks = self._fallback_risks(
            analysis=analysis,
            metrics=metrics,
            focus_sessions=focus_sessions,
        )
        recommendations = self._fallback_recommendations(
            analysis=analysis,
            weekly_metrics=weekly_metrics,
        )

        return WeeklyReviewAgentResult(
            summary=summary,
            insights=insights[:5],
            risks=risks[:5],
            recommendations=recommendations[:5],
            metrics=metrics,
            proposed_changes=analysis.proposed_changes[:5],
            analysis_status=analysis.status,
        )

    def validate_proposed_changes(
        self,
        raw_changes: object,
        *,
        stages: list[PlanStage],
    ) -> list[ProposedChange]:
        if not isinstance(raw_changes, list):
            return []

        stage_ids = {str(stage.id) for stage in stages}
        validated: list[ProposedChange] = []
        for raw_change in raw_changes:
            if len(validated) >= 5:
                break
            if not isinstance(raw_change, dict):
                continue
            if raw_change.get("type") not in ALLOWED_CHANGE_TYPES:
                continue
            try:
                change = ProposedChange.model_validate(raw_change)
            except ValidationError:
                continue

            if change.stage_id is None or str(change.stage_id) not in stage_ids:
                continue
            if not self._change_is_valid(change):
                continue
            validated.append(change)

        return validated

    def _change_is_valid(self, change: ProposedChange) -> bool:
        if not change.reason.strip():
            return False

        if change.type == "reschedule_stage":
            if (
                change.old_start_date is None
                or change.old_end_date is None
                or change.new_start_date is None
                or change.new_end_date is None
            ):
                return False
            return (
                change.old_end_date >= change.old_start_date
                and change.new_end_date >= change.new_start_date
            )

        if change.type == "split_stage":
            return bool(change.suggested_new_titles)

        if change.type == "adjust_stage_focus":
            return (
                change.suggested_focus_minutes_per_day is not None
                and change.suggested_focus_minutes_per_day > 0
            )

        if change.type == "mark_stage_at_risk":
            return change.risk_level in {"low", "medium", "high"}

        return False

    def _build_user_payload(
        self,
        *,
        plan: Plan,
        stages: list[PlanStage],
        metrics: AnalyticsMetrics | None,
        daily_breakdown: list[DailyBreakdownItem] | None,
        focus_sessions: list[FocusLog],
        analysis: RoadmapProgressAnalysis,
    ) -> str:
        payload = {
            "plan": {
                "id": str(plan.id),
                "title": plan.title,
                "status": plan.status,
                "generated_at": plan.generated_at.isoformat()
                if plan.generated_at
                else None,
                "adapted_at": plan.adapted_at.isoformat() if plan.adapted_at else None,
            },
            "stages": [
                {
                    "id": str(stage.id),
                    "title": stage.title,
                    "deliverable": stage.deliverable,
                    "status": stage.status,
                    "week_number": stage.week_number,
                    "order_index": stage.order_index,
                    "start_date": stage.start_date.isoformat()
                    if stage.start_date
                    else None,
                    "end_date": stage.end_date.isoformat() if stage.end_date else None,
                    "completed_at": stage.completed_at.isoformat()
                    if getattr(stage, "completed_at", None)
                    else None,
                }
                for stage in sorted(stages, key=lambda item: item.order_index)
            ],
            "weekly_metrics": (
                metrics.model_dump(mode="json", exclude={"plan_progress"})
                if metrics
                else None
            ),
            "focus_summary": self._focus_summary(focus_sessions),
            "daily_breakdown": (
                [item.model_dump(mode="json") for item in daily_breakdown]
                if daily_breakdown is not None
                else None
            ),
            "deterministic_analysis": {
                "status": analysis.status,
                "metrics": analysis.metrics.model_dump(mode="json"),
                "delayed_stage_ids": analysis.delayed_stage_ids,
                "proposed_changes": [
                    change.model_dump(mode="json")
                    for change in analysis.proposed_changes[:5]
                ],
            },
            "allowed_change_types": sorted(ALLOWED_CHANGE_TYPES),
            "expected_json": {
                "summary": "string",
                "insights": ["string"],
                "risks": ["string"],
                "recommendations": ["string"],
                "proposed_changes": [],
            },
            "rules": [
                "Use English.",
                "Do not include chain-of-thought.",
                "Do not create unsupported fields.",
                "Return at most 5 insights.",
                "Return at most 5 recommendations.",
                "Return at most 5 proposed changes.",
            ],
        }
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _fallback_insights(
        *,
        metrics: WeeklyReviewMetrics,
        stages: list[PlanStage],
        weekly_metrics: AnalyticsMetrics | None,
    ) -> list[str]:
        insights: list[str] = []
        if metrics.planned_focus_minutes is not None:
            insights.append(
                "You completed "
                f"{metrics.actual_focus_minutes} of "
                f"{metrics.planned_focus_minutes} planned focus minutes."
            )
        else:
            insights.append(
                f"You completed {metrics.actual_focus_minutes} focus minutes this week."
            )

        insights.append(
            "Roadmap progress is "
            f"{metrics.roadmap_progress_percent}% "
            f"({metrics.completed_stages_count} of {metrics.total_stages_count} "
            "stages completed)."
        )
        if metrics.completion_rate is not None:
            insights.append(
                f"Focus session completion rate was {metrics.completion_rate}%."
            )
        if weekly_metrics and weekly_metrics.streak_days:
            insights.append(
                f"Current focus streak is {weekly_metrics.streak_days} days."
            )
        if weekly_metrics and weekly_metrics.best_focus_hours:
            insights.append(
                "Best focus hours were "
                + ", ".join(weekly_metrics.best_focus_hours[:3])
                + "."
            )
        if weekly_metrics and weekly_metrics.most_focused_topics:
            topic = weekly_metrics.most_focused_topics[0]
            insights.append(
                f"Most attention went to {topic.topic} with {topic.minutes} minutes."
            )

        _ = stages
        return insights

    @staticmethod
    def _fallback_risks(
        *,
        analysis: RoadmapProgressAnalysis,
        metrics: WeeklyReviewMetrics,
        focus_sessions: list[FocusLog],
    ) -> list[str]:
        risks: list[str] = []
        if analysis.status == "behind":
            risks.append(
                "Unfinished planned stages may push next week's roadmap forward."
            )
        if (
            metrics.planned_focus_minutes is not None
            and metrics.actual_focus_minutes < metrics.planned_focus_minutes * 0.7
        ):
            risks.append("Actual focus time was below 70% of the planned target.")
        if metrics.completion_rate is not None and metrics.completion_rate < 70:
            risks.append("Focus session completion rate was below 70%.")
        if analysis.status == "insufficient_data" and not focus_sessions:
            risks.append("There are no plan-linked focus sessions for this period.")
        return risks

    @staticmethod
    def _fallback_recommendations(
        *,
        analysis: RoadmapProgressAnalysis,
        weekly_metrics: AnalyticsMetrics | None,
    ) -> list[str]:
        recommendations: list[str] = []
        if analysis.status == "insufficient_data":
            recommendations.append(
                "Log a few plan-linked focus sessions before relying on roadmap changes."
            )
        elif analysis.status == "behind":
            recommendations.append(
                "Reschedule unfinished planned stages before adding new scope."
            )
            recommendations.append(
                "Split the hardest delayed stage into smaller deliverables."
            )
        elif analysis.status == "ahead":
            recommendations.append(
                "Consider pulling the next stage forward or adding deeper practice."
            )
        else:
            recommendations.append(
                "Keep the current roadmap pace and protect the same focus rhythm."
            )

        if weekly_metrics and weekly_metrics.best_focus_hours:
            recommendations.append(
                f"Place complex work around {weekly_metrics.best_focus_hours[0]}."
            )
        return recommendations

    @staticmethod
    def _focus_summary(focus_sessions: list[FocusLog]) -> dict[str, object]:
        completed = [
            session for session in focus_sessions if session.status == "completed"
        ]
        cancelled = [
            session for session in focus_sessions if session.status == "cancelled"
        ]
        return {
            "completed_sessions_count": len(completed),
            "cancelled_sessions_count": len(cancelled),
            "actual_focus_minutes": sum(
                max(0, int(session.actual_duration_seconds or 0)) // 60
                for session in completed
            ),
            "topics": sorted(
                {
                    session.topic.strip()
                    for session in completed
                    if isinstance(session.topic, str) and session.topic.strip()
                }
            ),
        }

    @staticmethod
    def _period_from_metrics(
        weekly_metrics: AnalyticsMetricsResult | AnalyticsMetrics,
        timezone_name: str,
    ) -> ReviewPeriod:
        period = getattr(weekly_metrics, "period", None)
        if period is not None:
            return ReviewPeriod(
                start=period.start,
                end=period.end,
                timezone=period.timezone,
            )
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        return ReviewPeriod(
            start=start,
            end=start + timedelta(days=7),
            timezone=timezone_name,
        )

    @staticmethod
    def _metrics_from_weekly_metrics(
        weekly_metrics: AnalyticsMetricsResult | AnalyticsMetrics,
    ) -> AnalyticsMetrics | None:
        metrics = getattr(weekly_metrics, "metrics", None)
        if metrics is not None:
            return metrics
        if isinstance(weekly_metrics, AnalyticsMetrics):
            return weekly_metrics
        return None

    @staticmethod
    def _daily_breakdown_from_metrics(
        weekly_metrics: AnalyticsMetricsResult | AnalyticsMetrics,
    ) -> list[DailyBreakdownItem] | None:
        return getattr(weekly_metrics, "daily_breakdown", None)

    @staticmethod
    def _clean_text(value: object) -> str:
        return value.strip() if isinstance(value, str) else ""

    @classmethod
    def _clean_text_list(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [cleaned for item in value if (cleaned := cls._clean_text(item))]


weekly_review_agent = WeeklyReviewAgent()


__all__ = ["WeeklyReviewAgent", "WeeklyReviewAgentResult", "weekly_review_agent"]
