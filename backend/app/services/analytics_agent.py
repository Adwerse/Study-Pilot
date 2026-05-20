import json
import logging

from app.agents.llm_client import complete
from app.config import settings
from app.schemas.analytics import (
    AnalyticsDataQuality,
    AnalyticsMetrics,
    AnalyticsNarrative,
    AnalyticsPeriod,
    DailyBreakdownItem,
)


logger = logging.getLogger(__name__)


ANALYTICS_SYSTEM_PROMPT = (
    "You are the Analytics Agent for StudyPilot. Generate a concise report "
    "about the user's learning activity using only the supplied metrics. "
    "Do not invent data. If data is limited, explicitly say the conclusions "
    "are preliminary. Return JSON: "
    '{"summary": "...", "recommendations": ["...", "..."]}'
)


class AnalyticsAgent:
    async def generate_report(
        self,
        period: AnalyticsPeriod,
        metrics: AnalyticsMetrics,
        daily_breakdown: list[DailyBreakdownItem] | None = None,
        data_quality: AnalyticsDataQuality = AnalyticsDataQuality.medium,
    ) -> AnalyticsNarrative:
        if not settings.ANALYTICS_AI_ENABLED or not settings.TENSORIX_API_KEY:
            return self.generate_fallback_report(
                period=period,
                metrics=metrics,
                daily_breakdown=daily_breakdown,
                data_quality=data_quality,
            )

        try:
            raw = await complete(
                messages=[
                    {"role": "system", "content": ANALYTICS_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": self._build_user_prompt(
                            period=period,
                            metrics=metrics,
                            daily_breakdown=daily_breakdown,
                        ),
                    },
                ],
                model=settings.ANALYTICS_MODEL or settings.TENSORIX_MODEL,
                temperature=0.4,
                max_tokens=900,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(raw)
            narrative = AnalyticsNarrative.model_validate(parsed)
            return AnalyticsNarrative(
                summary=narrative.summary.strip(),
                recommendations=[
                    item.strip()
                    for item in narrative.recommendations[:4]
                    if item.strip()
                ],
            )
        except Exception:
            logger.exception("Analytics LLM narrative generation failed")
            return self.generate_fallback_report(
                period=period,
                metrics=metrics,
                daily_breakdown=daily_breakdown,
                data_quality=data_quality,
            )

    def generate_fallback_report(
        self,
        period: AnalyticsPeriod,
        metrics: AnalyticsMetrics,
        daily_breakdown: list[DailyBreakdownItem] | None = None,
        data_quality: AnalyticsDataQuality = AnalyticsDataQuality.medium,
    ) -> AnalyticsNarrative:
        _ = daily_breakdown
        period_label = "today" if period.type.value == "daily" else "this week"
        cautious_prefix = (
            "Data is still limited, so these conclusions are preliminary. "
            if data_quality == AnalyticsDataQuality.low
            else ""
        )

        if metrics.total_focus_minutes == 0:
            summary = (
                f"{cautious_prefix}There are no completed focus sessions with "
                "productive time in the selected period. I will not draw "
                "conclusions about best hours or topics without data."
            )
        else:
            summary_parts = [
                f"{cautious_prefix}You logged {metrics.total_focus_minutes} focus minutes {period_label}.",
                f"Completed sessions: {metrics.sessions_count}, cancelled: {metrics.cancelled_sessions_count}.",
                f"Current streak: {metrics.streak_days} days.",
            ]
            if metrics.completion_rate and data_quality != AnalyticsDataQuality.low:
                summary_parts.append(f"Completion rate: {metrics.completion_rate}%.")
            if metrics.most_focused_topics:
                top_topic = metrics.most_focused_topics[0]
                summary_parts.append(
                    f"Most time went to {top_topic.topic}: {top_topic.minutes} minutes."
                )
            summary = " ".join(summary_parts)

        recommendations = self._fallback_recommendations(metrics)
        return AnalyticsNarrative(summary=summary, recommendations=recommendations)

    def _build_user_prompt(
        self,
        period: AnalyticsPeriod,
        metrics: AnalyticsMetrics,
        daily_breakdown: list[DailyBreakdownItem] | None,
    ) -> str:
        return "\n".join(
            [
                "Metrics:",
                metrics.model_dump_json(),
                "",
                "Daily breakdown:",
                json.dumps(
                    [item.model_dump(mode="json") for item in daily_breakdown]
                    if daily_breakdown is not None
                    else None,
                    ensure_ascii=False,
                ),
                "",
                "Period:",
                period.model_dump_json(),
                "",
                "Rules:",
                "- do not add metrics that are not present in the input data;",
                "- do not promise guaranteed outcomes;",
                "- recommendations must be concrete;",
                "- answer in English;",
                "- maximum 4 recommendations.",
            ]
        )

    def _fallback_recommendations(self, metrics: AnalyticsMetrics) -> list[str]:
        recommendations: list[str] = []
        if metrics.total_focus_minutes == 0:
            recommendations.append("Start with one short 15-25 minute block.")

        if metrics.best_focus_hours:
            recommendations.append(
                f"Plan difficult tasks around {metrics.best_focus_hours[0]}."
            )

        if (
            metrics.completion_rate < 70
            and (metrics.sessions_count + metrics.cancelled_sessions_count) > 0
        ):
            recommendations.append(
                "Shorten focus blocks or schedule fewer sessions at once."
            )

        if metrics.most_focused_topics:
            top_topic = metrics.most_focused_topics[0].topic
            recommendations.append(
                f"Continue with {top_topic} while momentum is there."
            )

        if not recommendations:
            recommendations.append(
                "Plan the next focus block in advance and keep one clear goal."
            )

        return recommendations[:4]


analytics_agent = AnalyticsAgent()


__all__ = ["AnalyticsAgent", "analytics_agent"]
