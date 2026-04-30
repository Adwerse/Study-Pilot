def build_focus_end_message(*, topic: str | None, planned_duration_minutes: int) -> str:
    lines = ["Фокус-сессия завершена ✅", ""]

    if topic:
        lines.append(f"Тема: {topic}")

    lines.extend(
        [
            f"Время: {planned_duration_minutes} мин",
            "",
            "Пора сделать короткую паузу.",
        ]
    )
    return "\n".join(lines)


def build_break_end_message() -> str:
    return "Пауза закончилась ☕️\n\nГотов к следующему фокус-блоку? 🚀"
