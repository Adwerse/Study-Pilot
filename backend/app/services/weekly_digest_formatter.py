from app.schemas.analytics import AnalyticsDataQuality, TopicFocusMetric
from app.schemas.weekly_digest import WeeklyDigestReport


MAX_DIGEST_CHARS = 2400


class WeeklyDigestFormatter:
    def format(
        self,
        report: WeeklyDigestReport,
        *,
        include_analytics_link: bool = True,
    ) -> str:
        metrics = report.metrics
        lines = [
            "📊 Недельный отчёт StudyPilot",
            "",
            f"Фокус: {self._format_minutes(metrics.total_focus_minutes)}",
            f"Сессии: {metrics.sessions_count}",
            f"Completion rate: {metrics.completion_rate}%",
            f"Streak: {metrics.streak_days} {self._plural_days(metrics.streak_days)}",
        ]

        if report.data_quality == AnalyticsDataQuality.low:
            lines.extend(
                [
                    "",
                    "Данных пока мало, поэтому выводы предварительные.",
                ]
            )

        if metrics.best_focus_hours:
            lines.extend(["", f"Лучшие часы: {', '.join(metrics.best_focus_hours)}"])

        if metrics.most_focused_topics:
            lines.extend(["", "Темы недели:"])
            lines.extend(
                f"• {topic.topic} — {self._format_minutes(topic.minutes)}"
                for topic in self._top_topics(metrics.most_focused_topics)
            )

        if report.summary.strip():
            lines.extend(["", "Итог:", report.summary.strip()])

        recommendations = [
            item.strip() for item in report.recommendations[:4] if item.strip()
        ]
        if recommendations:
            lines.extend(["", "Рекомендации:"])
            lines.extend(
                f"{index}. {recommendation}"
                for index, recommendation in enumerate(recommendations, start=1)
            )

        if include_analytics_link:
            lines.extend(["", "Открыть аналитику 👇"])
        return self._trim("\n".join(lines).strip())

    @staticmethod
    def _format_minutes(minutes: int) -> str:
        safe_minutes = max(0, int(minutes))
        hours, remainder = divmod(safe_minutes, 60)
        if hours:
            return f"{hours}ч {remainder:02d}м"
        return f"{remainder}м"

    @staticmethod
    def _plural_days(days: int) -> str:
        value = abs(days) % 100
        last_digit = value % 10
        if 11 <= value <= 14:
            return "дней"
        if last_digit == 1:
            return "день"
        if 2 <= last_digit <= 4:
            return "дня"
        return "дней"

    @staticmethod
    def _top_topics(topics: list[TopicFocusMetric]) -> list[TopicFocusMetric]:
        return topics[:5]

    @staticmethod
    def _trim(text: str) -> str:
        if len(text) <= MAX_DIGEST_CHARS:
            return text
        return f"{text[: MAX_DIGEST_CHARS - 3].rstrip()}..."
