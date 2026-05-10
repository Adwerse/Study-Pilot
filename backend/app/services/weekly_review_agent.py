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
    "Ты Weekly Review Agent приложения StudyPilot. Твоя задача - сравнить "
    "учебный план пользователя с фактическим прогрессом за неделю и предложить "
    "безопасные улучшения roadmap. Отвечай только на основе переданных данных. "
    "Не выдумывай факты, completed stages, даты или минуты фокуса. Если данных "
    "мало, скажи это явно. Верни только JSON."
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
        timezone_name = timezone.key if isinstance(timezone, ZoneInfo) else str(timezone)
        period = period or self._period_from_metrics(weekly_metrics, timezone_name)
        analytics_metrics = self._metrics_from_weekly_metrics(weekly_metrics)
        daily_breakdown = daily_breakdown or self._daily_breakdown_from_metrics(weekly_metrics)

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
                model=settings.WEEKLY_REVIEW_MODEL or settings.ANALYTICS_MODEL or settings.TENSORIX_MODEL,
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
                insights=self._clean_text_list(parsed.get("insights")) or fallback.insights,
                risks=self._clean_text_list(parsed.get("risks")) or fallback.risks,
                recommendations=(
                    self._clean_text_list(parsed.get("recommendations"))
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
                "Данных за неделю пока мало: нет завершенных focus-сессий и "
                "нет подтвержденного прогресса по этапам."
            )
        elif analysis.status == "behind":
            summary = (
                "Roadmap отстает от плана: завершенных этапов меньше, чем "
                "ожидалось к концу недели."
            )
        elif analysis.status == "ahead":
            summary = "Roadmap идет быстрее плана: завершено больше этапов, чем ожидалось."
        else:
            summary = "Roadmap идет по плану: фактический прогресс совпадает с ожиданиями."

        insights = [
            f"Фокус за неделю: {metrics.actual_focus_minutes} мин.",
            (
                f"Этапы: завершено {metrics.completed_stages_count} "
                f"из {len(stages)}, прогресс roadmap {metrics.roadmap_progress_percent}%."
            ),
        ]
        if metrics.planned_focus_minutes is not None:
            insights.insert(
                0,
                (
                    f"Ты выполнил {metrics.actual_focus_minutes} минут фокуса "
                    f"из ожидаемых {metrics.planned_focus_minutes}."
                ),
            )
        if weekly_metrics and weekly_metrics.best_focus_hours:
            insights.append(
                "Лучшие часы фокуса: " + ", ".join(weekly_metrics.best_focus_hours) + "."
            )
        if weekly_metrics and weekly_metrics.most_focused_topics:
            topic = weekly_metrics.most_focused_topics[0]
            insights.append(f"Самая заметная тема: {topic.topic}, {topic.minutes} мин.")

        risks: list[str] = []
        if analysis.status == "behind":
            risks.append("Есть риск сдвига следующих этапов без корректировки дат.")
        if weekly_metrics and weekly_metrics.completion_rate < 70 and focus_sessions:
            risks.append("Completion rate ниже 70%, часть focus-сессий отменяется.")

        recommendations: list[str] = []
        if analysis.status == "insufficient_data":
            recommendations.append(
                "Запланируй 1-2 короткие focus-сессии и вернись к review после фактических данных."
            )
        elif analysis.status == "behind":
            recommendations.append("Сдвинь незавершенные этапы и уменьши объем ближайшей недели.")
            recommendations.append("Разбей самый сложный этап на меньшие проверяемые блоки.")
        elif analysis.status == "ahead":
            recommendations.append("Можно ускорить следующий этап или добавить углубляющую практику.")
        else:
            recommendations.append("Сохрани текущий ритм и планируй сложные блоки на лучшие часы фокуса.")

        if weekly_metrics and weekly_metrics.best_focus_hours:
            recommendations.append(
                f"Ставь сложные блоки на {weekly_metrics.best_focus_hours[0]}."
            )

        return WeeklyReviewAgentResult(
            summary=summary,
            insights=insights[:5],
            risks=risks[:4],
            recommendations=recommendations[:5],
            metrics=metrics,
            proposed_changes=analysis.proposed_changes,
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
            return change.old_end_date >= change.old_start_date and change.new_end_date >= change.new_start_date

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
                "generated_at": plan.generated_at.isoformat() if plan.generated_at else None,
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
                    "start_date": stage.start_date.isoformat() if stage.start_date else None,
                    "end_date": stage.end_date.isoformat() if stage.end_date else None,
                }
                for stage in sorted(stages, key=lambda item: item.order_index)
            ],
            "weekly_metrics": metrics.model_dump(mode="json") if metrics else None,
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
                    change.model_dump(mode="json") for change in analysis.proposed_changes
                ],
            },
            "allowed_change_types": sorted(ALLOWED_CHANGE_TYPES),
        }
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _focus_summary(focus_sessions: list[FocusLog]) -> dict[str, object]:
        completed = [session for session in focus_sessions if session.status == "completed"]
        cancelled = [session for session in focus_sessions if session.status == "cancelled"]
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
        return ReviewPeriod(start=start, end=start + timedelta(days=7), timezone=timezone_name)

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
