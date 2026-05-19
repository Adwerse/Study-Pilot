import json

from app.agents.llm_client import complete
from app.agents.prompts.daily_coach import DAILY_COACH_SYSTEM, DAILY_COACH_USER
from app.config import settings
from app.schemas.focus_block import FocusBlock
from app.schemas.focus_block import DailyPlan
from app.schemas.plan import PlanStage


class DailyCoachAgent:
    async def generate_plan(
        self,
        stage: PlanStage,
        completed_today: int = 0,
        minutes_today: int = 0,
        topics_today: list[str] | None = None,
        available_hours: float = 2.0,
    ) -> DailyPlan:
        if settings.LLM_PROVIDER == "fake":
            return DailyPlan(
                blocks=[
                    FocusBlock(
                        title=f"Practice {stage.title}",
                        topic=stage.title,
                        duration_minutes=25,
                        description="Complete one focused exercise for this stage.",
                        priority=1,
                    ),
                    FocusBlock(
                        title="Write learning notes",
                        topic="Reflection",
                        duration_minutes=25,
                        description="Capture what worked and one open question.",
                        priority=2,
                    ),
                ],
                daily_note="Use one short focus loop and keep the result visible.",
            )

        topics_str = (
            ", ".join(stage.topics)
            if hasattr(stage, "topics") and stage.topics
            else "not specified"
        )
        done_topics_str = ", ".join(topics_today or []) or "none"

        user_msg = DAILY_COACH_USER.format(
            stage_title=stage.title,
            stage_deliverable=stage.deliverable,
            stage_topics=topics_str,
            completed_today=completed_today,
            minutes_today=minutes_today,
            topics_today=done_topics_str,
            available_hours=available_hours,
        )

        raw = await complete(
            messages=[
                {"role": "system", "content": DAILY_COACH_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.5,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM returned invalid JSON: {e}\\nRaw: {raw[:300]}"
            ) from e

        return DailyPlan.model_validate(data)


daily_coach_agent = DailyCoachAgent()
