from unittest.mock import AsyncMock, patch

import pytest

from app.agents.daily_coach import DailyCoachAgent
from app.schemas.plan import PlanStage


MOCK_LLM_RESPONSE = '''
{
  "blocks": [
    {
      "title": "Разобрать переменные и типы",
      "topic": "Основы Python",
      "duration_minutes": 25,
      "description": "Изучить int, str, list, dict",
      "priority": 1
    },
    {
      "title": "Написать первый скрипт",
      "topic": "Практика",
      "duration_minutes": 40,
      "description": "Hello world и базовые операции",
      "priority": 2
    }
  ],
  "daily_note": "Отличное начало — два блока хватит для первого дня."
}
'''


@pytest.fixture
def mock_stage() -> PlanStage:
    return PlanStage(
        id="test-1",
        plan_id="plan-1",
        week_number=1,
        title="Основы Python",
        deliverable="Написать первый скрипт",
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
        new=AsyncMock(return_value="это не json"),
    ):
        agent = DailyCoachAgent()
        with pytest.raises(ValueError, match="невалидный JSON"):
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
            topics_today=["Переменные", "Типы данных"],
        )

    assert "Переменные" in captured["user_msg"]
    assert "Типы данных" in captured["user_msg"]
