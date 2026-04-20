from unittest.mock import AsyncMock, patch

import pytest

from app.api.dependencies import get_current_user
from app.repositories.runtime_store import reset_runtime_state
from app.schemas.focus_block import DailyPlan, FocusBlock


@pytest.fixture(autouse=True)
def runtime_state_cleanup() -> None:
    reset_runtime_state()
    yield
    reset_runtime_state()


@pytest.fixture(autouse=True)
def override_auth(app) -> None:
    async def fake_current_user() -> dict:
        return {
            "id": 123456,
            "username": "tester",
            "first_name": "Test",
        }

    app.dependency_overrides[get_current_user] = fake_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_plan_persists_between_requests(client) -> None:
    mock_roadmap = {
        "title": "Python Starter Plan",
        "total_weeks": 2,
        "stages": [
            {
                "week_number": 1,
                "title": "Python Basics",
                "deliverable": "Write basic scripts",
                "topics": ["Variables", "Types"],
            },
            {
                "week_number": 2,
                "title": "Functions",
                "deliverable": "Build CLI helper",
                "topics": ["Functions", "Modules"],
            },
        ],
    }

    with patch("app.agents.roadmap.roadmap_agent.generate", new=AsyncMock(return_value=mock_roadmap)):
        create_response = await client.post(
            "/api/v1/plans/",
            json={
                "goal": "Learn Python",
                "level": "beginner",
                "weekly_hours": 6,
            },
        )

    assert create_response.status_code == 200
    created_plan = create_response.json()
    assert created_plan["title"] == "Python Starter Plan"
    assert len(created_plan["stages"]) == 2
    assert created_plan["stages"][0]["status"] == "in_progress"

    current_response = await client.get("/api/v1/plans/current")
    assert current_response.status_code == 200
    current_plan = current_response.json()
    assert current_plan is not None
    assert current_plan["id"] == created_plan["id"]


@pytest.mark.asyncio
async def test_daily_plan_uses_current_stage_and_focus_history(client) -> None:
    mock_roadmap = {
        "title": "Python Starter Plan",
        "total_weeks": 1,
        "stages": [
            {
                "week_number": 1,
                "title": "Python Basics",
                "deliverable": "Write basic scripts",
                "topics": ["Variables", "Types"],
            }
        ],
    }

    with patch("app.agents.roadmap.roadmap_agent.generate", new=AsyncMock(return_value=mock_roadmap)):
        create_response = await client.post(
            "/api/v1/plans/",
            json={
                "goal": "Learn Python",
                "level": "beginner",
                "weekly_hours": 6,
            },
        )

    assert create_response.status_code == 200
    created_plan = create_response.json()
    stage_id = created_plan["stages"][0]["id"]

    start_response = await client.post(
        "/api/v1/focus/start",
        json={
            "topic": "Variables",
            "stage_id": stage_id,
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["id"]

    end_response = await client.post(
        "/api/v1/focus/end",
        json={
            "session_id": session_id,
            "difficulty": 3,
        },
    )
    assert end_response.status_code == 200

    captured: dict[str, object] = {}

    async def fake_generate_plan(**kwargs):
        captured.update(kwargs)
        return DailyPlan(
            blocks=[
                FocusBlock(
                    title="Practice variables",
                    topic="Variables",
                    duration_minutes=25,
                    description="Solve simple tasks",
                    priority=1,
                ),
                FocusBlock(
                    title="Read about functions",
                    topic="Functions",
                    duration_minutes=25,
                    description="Review function syntax",
                    priority=2,
                ),
            ],
            daily_note="Keep momentum.",
        )

    with patch("app.agents.daily_coach.daily_coach_agent.generate_plan", new=fake_generate_plan):
        today_response = await client.get("/api/v1/plans/current/today")

    assert today_response.status_code == 200
    assert captured["stage"].title == "Python Basics"
    assert captured["completed_today"] == 1
    assert "Variables" in captured["topics_today"]
