import json
from datetime import date

from app.agents.llm_client import complete
from app.agents.prompts.roadmap import ROADMAP_SYSTEM, ROADMAP_USER
from app.config import settings
from app.schemas.plan import PlanCreate
from app.schemas.plan_stage import PlanStageCreate


class RoadmapAgent:
    async def generate(
        self,
        goal: str,
        level: str,
        weekly_hours: int,
        deadline: date | None,
    ) -> dict:
        if settings.LLM_PROVIDER == "fake":
            return self._fake_roadmap(goal=goal)

        deadline_str = deadline.isoformat() if deadline else "not set"
        user_msg = ROADMAP_USER.format(
            goal=goal,
            level=level,
            weekly_hours=weekly_hours,
            deadline=deadline_str,
        )
        raw = await complete(
            messages=[
                {"role": "system", "content": ROADMAP_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.6,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM returned invalid JSON: {e}\\nRaw: {raw[:300]}"
            ) from e

        self._validate(data)
        return data

    def _validate(self, data: dict) -> None:
        required = {"title", "total_weeks", "stages"}
        missing = required - data.keys()
        if missing:
            raise ValueError(f"Missing required fields in LLM response: {missing}")
        if not isinstance(data["stages"], list) or len(data["stages"]) == 0:
            raise ValueError("stages must be a non-empty list")
        for s in data["stages"]:
            for field in ("week_number", "title", "deliverable"):
                if field not in s:
                    raise ValueError(f"Stage is missing field: {field}")

    @staticmethod
    def _fake_roadmap(goal: str) -> dict:
        return {
            "title": f"{goal.strip()[:80]} Roadmap",
            "total_weeks": 3,
            "stages": [
                {
                    "week_number": 1,
                    "title": "Foundations",
                    "deliverable": "Build a small baseline project",
                    "topics": ["Basics", "Practice"],
                    "hours_required": 4,
                },
                {
                    "week_number": 2,
                    "title": "Guided Practice",
                    "deliverable": "Complete one guided exercise",
                    "topics": ["Patterns", "Feedback"],
                    "hours_required": 5,
                },
                {
                    "week_number": 3,
                    "title": "Review And Ship",
                    "deliverable": "Summarize progress and next steps",
                    "topics": ["Review", "Iteration"],
                    "hours_required": 3,
                },
            ],
        }


# Keep schema symbols imported for upcoming DB persistence integration in sprint continuation.
_ = (PlanCreate, PlanStageCreate)


roadmap_agent = RoadmapAgent()
