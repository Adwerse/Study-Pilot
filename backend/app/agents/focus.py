from datetime import datetime, timezone

from app.models.focus_log import FocusLog


POMODORO_DURATION = 25
SHORT_BREAK = 5
LONG_BREAK = 15
SESSIONS_BEFORE_LONG_BREAK = 4


class FocusAgent:
    def format_start_message(self, session: FocusLog) -> str:
        return (
            "Focus session started\n"
            f"Topic: {session.topic}\n"
            f"Timer: {POMODORO_DURATION} minutes\n\n"
            "Put your phone away. Focus."
        )

    def format_end_message(self, session: FocusLog, sessions_today: int) -> str:
        duration = session.duration_minutes or 0
        needs_long = sessions_today % SESSIONS_BEFORE_LONG_BREAK == 0
        break_time = LONG_BREAK if needs_long else SHORT_BREAK
        break_type = "long break" if needs_long else "short break"
        return (
            "Focus session completed\n"
            f"Topic: {session.topic}\n"
            f"Duration: {duration} min\n"
            f"Sessions today: {sessions_today}\n\n"
            f"Take a {break_type} - {break_time} minutes."
        )

    def should_send_reminder(
        self, started_at: datetime, threshold_minutes: int = 50
    ) -> bool:
        elapsed = (datetime.now(timezone.utc) - started_at).total_seconds() / 60
        return elapsed >= threshold_minutes


focus_agent = FocusAgent()
