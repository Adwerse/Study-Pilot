from unittest.mock import AsyncMock, patch

import pytest

from app.agents.daily_coach import DailyCoachAgent
from app.schemas.plan import PlanStage


MOCK_LLM_RESPONSE = '''
{
  "blocks": [
    {
      "title": "Review variables and types",
      "topic": "Python fundamentals",
      "duration_minutes": 25,
      "description": "Study int, str, list, and dict",
      "priority": 1
    },
    {
      "title": "Write the first script",
      "topic": "Practice",
      "duration_minutes": 40,
      "description": "Hello world and basic operations",
      "priority": 2
    }
  ],
  "daily_note": "Great start. Two blocks are enough for the first day."
}
'''


@pytest.fixture
def mock_stage() -> PlanStage:
    return PlanStage(
        id="test-1",
        plan_id="plan-1",
        week_number=1,
        title="Python fundamentals",
        deliverable="Write the first script",
        status="in_progress",
        order_index=0,
    )


@pytest.mark.asyncio
async def test_generate_plan_returns_valid_structure(mock_stage: PlanStage) -> None:
    with patch(
        "app.agents.daily_coach.complete",
        new=AsyncMock(return_value=MOCK_LLM_RESPONSE),
    ):
        agent = DailyCoachAgent()
        result = await agent.generate_plan(stage=mock_stage)

    assert len(result.blocks) == 2
    assert result.blocks[0].priority == 1
    assert result.blocks[0].duration_minutes == 25
    assert isinstance(result.daily_note, str)
    assert len(result.daily_note) > 0


@pytest.mark.asyncio
async def test_blocks_count_within_bounds(mock_stage: PlanStage) -> None:
    with patch(
        "app.agents.daily_coach.complete",
        new=AsyncMock(return_value=MOCK_LLM_RESPONSE),
    ):
        agent = DailyCoachAgent()
        result = await agent.generate_plan(stage=mock_stage)

    assert 2 <= len(result.blocks) <= 4


@pytest.mark.asyncio
async def test_invalid_json_raises_value_error(mock_stage: PlanStage) -> None:
    with patch(
        "app.agents.daily_coach.complete",
        new=AsyncMock(return_value="this is not json"),
    ):
        agent = DailyCoachAgent()
        with pytest.raises(ValueError, match="invalid JSON"):
            await agent.generate_plan(stage=mock_stage)


@pytest.mark.asyncio
async def test_topics_today_passed_to_prompt(mock_stage: PlanStage) -> None:
    captured: dict[str, str] = {}

    async def capture_complete(messages: list[dict], **kwargs: object) -> str:
        _ = kwargs
        captured["user_msg"] = messages[-1]["content"]
        return MOCK_LLM_RESPONSE

    with patch("app.agents.daily_coach.complete", new=capture_complete):
        agent = DailyCoachAgent()
        await agent.generate_plan(
            stage=mock_stage,
            topics_today=["Variables", "Data types"],
        )

    assert "Variables" in captured["user_msg"]
    assert "Data types" in captured["user_msg"]
