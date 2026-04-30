def build_focus_end_message(*, topic: str | None, planned_duration_minutes: int) -> str:
    lines = ["Focus session completed ✅", ""]

    if topic:
        lines.append(f"Topic: {topic}")

    lines.extend(
        [
            f"Duration: {planned_duration_minutes} min",
            "",
            "Time for a short break.",
        ]
    )
    return "\n".join(lines)


def build_break_end_message() -> str:
    return "Break is over ☕️\n\nReady for the next focus block? 🚀"
