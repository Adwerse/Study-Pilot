from copy import deepcopy
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from app.schemas.focus_session import FocusSession


_user_plans: dict[str, dict[str, Any]] = {}
_user_focus_history: dict[str, list[FocusSession]] = {}
_user_active_focus: dict[str, FocusSession] = {}


def reset_runtime_state() -> None:
    _user_plans.clear()
    _user_focus_history.clear()
    _user_active_focus.clear()


def get_user_key(current_user: dict[str, Any]) -> str:
    user_id = current_user.get("id")
    return str(user_id) if user_id is not None else "anonymous"


def _normalize_topics(topics: Any) -> list[str]:
    if not isinstance(topics, list):
        return []

    cleaned_topics: list[str] = []
    for item in topics:
        if isinstance(item, str) and item.strip():
            cleaned_topics.append(item.strip())
    return cleaned_topics


def save_plan(user_key: str, roadmap_result: dict[str, Any]) -> dict[str, Any]:
    plan_id = str(uuid4())
    stages_raw = roadmap_result.get("stages", [])
    now_iso = datetime.now(timezone.utc).isoformat()

    stages: list[dict[str, Any]] = []
    for index, stage_raw in enumerate(stages_raw if isinstance(stages_raw, list) else []):
        if not isinstance(stage_raw, dict):
            continue

        week_number = stage_raw.get("week_number", index + 1)
        if not isinstance(week_number, int):
            try:
                week_number = int(week_number)
            except (TypeError, ValueError):
                week_number = index + 1

        stage_status = stage_raw.get("status")
        if stage_status not in {"pending", "in_progress", "done"}:
            stage_status = "in_progress" if index == 0 else "pending"

        stage: dict[str, Any] = {
            "id": str(uuid4()),
            "plan_id": plan_id,
            "week_number": week_number,
            "title": str(stage_raw.get("title") or f"Week {index + 1}"),
            "deliverable": str(stage_raw.get("deliverable") or ""),
            "status": stage_status,
            "order_index": index,
            "topics": _normalize_topics(stage_raw.get("topics")),
        }

        hours_required = stage_raw.get("hours_required")
        if isinstance(hours_required, (int, float)):
            stage["hours_required"] = int(hours_required)

        stages.append(stage)

    if stages and not any(stage["status"] == "in_progress" for stage in stages):
        stages[0]["status"] = "in_progress"

    total_weeks = roadmap_result.get("total_weeks", len(stages))
    if not isinstance(total_weeks, int):
        try:
            total_weeks = int(total_weeks)
        except (TypeError, ValueError):
            total_weeks = len(stages)

    plan = {
        "id": plan_id,
        "user_id": user_key,
        "title": str(roadmap_result.get("title") or "Learning Plan"),
        "status": "active",
        "generated_at": now_iso,
        "adapted_at": None,
        "total_weeks": total_weeks,
        "stages": stages,
    }

    _user_plans[user_key] = plan
    return deepcopy(plan)


def get_plan(user_key: str) -> dict[str, Any] | None:
    plan = _user_plans.get(user_key)
    return deepcopy(plan) if plan else None


def get_current_stage(user_key: str) -> dict[str, Any] | None:
    plan = _user_plans.get(user_key)
    if not plan:
        return None

    stages = plan.get("stages")
    if not isinstance(stages, list):
        return None

    for stage in stages:
        if isinstance(stage, dict) and stage.get("status") == "in_progress":
            return deepcopy(stage)

    return deepcopy(stages[0]) if stages else None


def start_focus_session(user_key: str, topic: str, stage_id: str | None) -> FocusSession:
    active = _user_active_focus.get(user_key)
    if active and active.ended_at is None:
        return active.model_copy(deep=True)

    started_at = datetime.now(timezone.utc)
    session = FocusSession(
        id=str(uuid4()),
        user_id=user_key,
        stage_id=stage_id,
        started_at=started_at,
        topic=topic,
        completed=False,
    )

    _user_active_focus[user_key] = session
    _user_focus_history.setdefault(user_key, []).append(session)
    return session.model_copy(deep=True)


def end_focus_session(user_key: str, session_id: str, difficulty: int) -> FocusSession | None:
    active = _user_active_focus.get(user_key)
    if active and active.id == session_id and active.ended_at is None:
        ended_at = datetime.now(timezone.utc)
        duration_minutes = max(1, int((ended_at - active.started_at).total_seconds() // 60))

        active.ended_at = ended_at
        active.duration_minutes = duration_minutes
        active.difficulty = difficulty
        active.completed = True

        _user_active_focus.pop(user_key, None)
        return active.model_copy(deep=True)

    for session in reversed(_user_focus_history.get(user_key, [])):
        if session.id != session_id:
            continue

        if session.ended_at is None:
            ended_at = datetime.now(timezone.utc)
            duration_minutes = max(1, int((ended_at - session.started_at).total_seconds() // 60))
            session.ended_at = ended_at
            session.duration_minutes = duration_minutes
            session.difficulty = difficulty
            session.completed = True
            _user_active_focus.pop(user_key, None)

        return session.model_copy(deep=True)

    return None


def get_focus_history(user_key: str) -> list[FocusSession]:
    history = _user_focus_history.get(user_key, [])
    ordered = sorted(history, key=lambda item: item.started_at, reverse=True)
    return [item.model_copy(deep=True) for item in ordered]


def get_today_focus_summary(user_key: str, today_utc: date) -> tuple[int, int, list[str]]:
    history = _user_focus_history.get(user_key, [])
    completed_today: list[FocusSession] = []

    for session in history:
        if not session.completed:
            continue

        session_date = (session.ended_at or session.started_at).date()
        if session_date == today_utc:
            completed_today.append(session)

    completed_count = len(completed_today)
    minutes_total = sum(session.duration_minutes or 0 for session in completed_today)
    topics_today = sorted({session.topic for session in completed_today if session.topic})

    return completed_count, minutes_total, topics_today
