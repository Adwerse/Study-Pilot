import os

import pytest

from app.agents.daily_coach import daily_coach_agent
from app.schemas.plan import PlanStage


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("TENSORIX_API_KEY"),
    reason="TENSORIX_API_KEY не задан",
)
async def test_real_daily_plan_generation() -> None:
    stage = PlanStage(
        id="real-1",
        plan_id="plan-1",
        week_number=1,
        title="Основы Python",
        deliverable="Написать скрипт обработки данных",
        status="in_progress",
        order_index=0,
    )
    result = await daily_coach_agent.generate_plan(
        stage=stage,
        completed_today=1,
        minutes_today=30,
        topics_today=["Переменные"],
        available_hours=2.0,
    )
    assert 2 <= len(result.blocks) <= 4
    for block in result.blocks:
        assert 15 <= block.duration_minutes <= 90
        assert 1 <= block.priority <= 4
        assert len(block.title) > 5

    print(f"\n✅ Сгенерировано блоков: {len(result.blocks)}")
    for block in result.blocks:
        print(f"   [{block.priority}] {block.title} ({block.duration_minutes} мин)")
    print(f"   Заметка: {result.daily_note}")
