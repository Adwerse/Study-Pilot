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
    "Ты Analytics Agent приложения StudyPilot. Сгенерируй краткий отчёт по "
    "учебной активности пользователя только на основе переданных метрик. "
    "Не выдумывай данные. Если данных мало, явно скажи, что выводы "
    "предварительные. Верни JSON: "
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
        period_label = "сегодня" if period.type.value == "daily" else "за неделю"
        cautious_prefix = (
            "Данных пока мало, выводы предварительные. "
            if data_quality == AnalyticsDataQuality.low
            else ""
        )

        if metrics.total_focus_minutes == 0:
            summary = (
                f"{cautious_prefix}За выбранный период нет завершённых "
                "фокус-сессий с продуктивным временем. Я не буду делать выводы "
                "о лучших часах или темах без данных."
            )
        else:
            summary_parts = [
                f"{cautious_prefix}Ты набрал {metrics.total_focus_minutes} минут фокуса {period_label}.",
                f"Завершённых сессий: {metrics.sessions_count}, отменённых: {metrics.cancelled_sessions_count}.",
                f"Текущий streak: {metrics.streak_days} дн.",
            ]
            if metrics.completion_rate and data_quality != AnalyticsDataQuality.low:
                summary_parts.append(f"Completion rate: {metrics.completion_rate}%.")
            if metrics.most_focused_topics:
                top_topic = metrics.most_focused_topics[0]
                summary_parts.append(
                    f"Больше всего времени ушло на тему «{top_topic.topic}»: {top_topic.minutes} мин."
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
                "Метрики:",
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
                "Период:",
                period.model_dump_json(),
                "",
                "Правила:",
                "- не добавляй метрики, которых нет во входных данных;",
                "- не обещай гарантированный результат;",
                "- рекомендации должны быть конкретными;",
                "- язык ответа - русский;",
                "- максимум 4 рекомендации.",
            ]
        )

    def _fallback_recommendations(self, metrics: AnalyticsMetrics) -> list[str]:
        recommendations: list[str] = []
        if metrics.total_focus_minutes == 0:
            recommendations.append("Начни с одного короткого блока на 15-25 минут.")

        if metrics.best_focus_hours:
            recommendations.append(
                f"Планируй сложные задачи на {metrics.best_focus_hours[0]}."
            )

        if (
            metrics.completion_rate < 70
            and (metrics.sessions_count + metrics.cancelled_sessions_count) > 0
        ):
            recommendations.append(
                "Снизь размер фокус-блока или ставь меньше сессий за раз."
            )

        if metrics.most_focused_topics:
            top_topic = metrics.most_focused_topics[0].topic
            recommendations.append(f"Продолжи с темы «{top_topic}», пока есть инерция.")

        if not recommendations:
            recommendations.append(
                "Запланируй следующий фокус-блок заранее и оставь одну понятную цель."
            )

        return recommendations[:4]


analytics_agent = AnalyticsAgent()


__all__ = ["AnalyticsAgent", "analytics_agent"]
