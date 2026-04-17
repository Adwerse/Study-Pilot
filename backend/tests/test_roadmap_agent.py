import os

import pytest

from app.agents.roadmap import roadmap_agent


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("TENSORIX_API_KEY"),
    reason="TENSORIX_API_KEY is not set",
)
async def test_roadmap_generation() -> None:
    result = await roadmap_agent.generate(
        goal="Learn Python fundamentals for data analysis",
        level="beginner",
        weekly_hours=8,
        deadline=None,
    )

    assert "title" in result
    assert "stages" in result
    assert isinstance(result["stages"], list)
    assert len(result["stages"]) > 0

    for stage in result["stages"]:
        assert "week_number" in stage
        assert "title" in stage
        assert "deliverable" in stage
        assert isinstance(stage["week_number"], int)
        assert len(stage["title"]) > 3
        assert len(stage["deliverable"]) > 10

    print(f"\nGenerated stages: {len(result['stages'])}")
    print(f"   Plan title: {result['title']}")
    print(f"   First stage: {result['stages'][0]['title']}")
    print(f"   Deliverable: {result['stages'][0]['deliverable']}")