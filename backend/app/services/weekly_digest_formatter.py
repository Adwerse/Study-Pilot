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
            "StudyPilot weekly report",
            "",
            f"Focus: {self._format_minutes(metrics.total_focus_minutes)}",
            f"Sessions: {metrics.sessions_count}",
            f"Completion rate: {metrics.completion_rate}%",
            f"Streak: {metrics.streak_days} {self._plural_days(metrics.streak_days)}",
        ]

        if report.data_quality == AnalyticsDataQuality.low:
            lines.extend(
                [
                    "",
                    "Data is still limited, so these conclusions are preliminary.",
                ]
            )

        if metrics.best_focus_hours:
            lines.extend(["", f"Best hours: {', '.join(metrics.best_focus_hours)}"])

        if metrics.most_focused_topics:
            lines.extend(["", "Topics this week:"])
            lines.extend(
                f"- {topic.topic}: {self._format_minutes(topic.minutes)}"
                for topic in self._top_topics(metrics.most_focused_topics)
            )

        if report.summary.strip():
            lines.extend(["", "Summary:", report.summary.strip()])

        recommendations = [
            item.strip() for item in report.recommendations[:4] if item.strip()
        ]
        if recommendations:
            lines.extend(["", "Recommendations:"])
            lines.extend(
                f"{index}. {recommendation}"
                for index, recommendation in enumerate(recommendations, start=1)
            )

        if include_analytics_link:
            lines.extend(["", "Open analytics:"])
        return self._trim("\n".join(lines).strip())

    @staticmethod
    def _format_minutes(minutes: int) -> str:
        safe_minutes = max(0, int(minutes))
        hours, remainder = divmod(safe_minutes, 60)
        if hours:
            return f"{hours}h {remainder:02d}m"
        return f"{remainder}m"

    @staticmethod
    def _plural_days(days: int) -> str:
        return "day" if abs(days) == 1 else "days"

    @staticmethod
    def _top_topics(topics: list[TopicFocusMetric]) -> list[TopicFocusMetric]:
        return topics[:5]

    @staticmethod
    def _trim(text: str) -> str:
        if len(text) <= MAX_DIGEST_CHARS:
            return text
        return f"{text[: MAX_DIGEST_CHARS - 3].rstrip()}..."
