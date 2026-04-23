from datetime import datetime, timezone

from app.models.focus_log import FocusLog


POMODORO_DURATION = 25
SHORT_BREAK = 5
LONG_BREAK = 15
SESSIONS_BEFORE_LONG_BREAK = 4


class FocusAgent:
    def format_start_message(self, session: FocusLog) -> str:
        return (
            f"🎯 Сессия началась\n"
            f"Тема: {session.topic}\n"
            f"Таймер: {POMODORO_DURATION} минут\n\n"
            f"Убери телефон. Фокус."
        )

    def format_end_message(self, session: FocusLog, sessions_today: int) -> str:
        duration = session.duration_minutes or 0
        needs_long = sessions_today % SESSIONS_BEFORE_LONG_BREAK == 0
        break_time = LONG_BREAK if needs_long else SHORT_BREAK
        break_type = "длинный перерыв" if needs_long else "короткий перерыв"
        return (
            f"✅ Сессия завершена\n"
            f"Тема: {session.topic}\n"
            f"Продолжительность: {duration} мин\n"
            f"Сессий сегодня: {sessions_today}\n\n"
            f"Возьми {break_type} — {break_time} минут."
        )

    def should_send_reminder(self, started_at: datetime, threshold_minutes: int = 50) -> bool:
        elapsed = (datetime.now(timezone.utc) - started_at).total_seconds() / 60
        return elapsed >= threshold_minutes


focus_agent = FocusAgent()
