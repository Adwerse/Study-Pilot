from datetime import date

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.agents.daily_coach import daily_coach_agent
from app.agents.roadmap import roadmap_agent
from app.api.dependencies import get_current_user
from app.schemas.focus_block import DailyPlan
from app.schemas.plan import PlanStage


router = APIRouter(prefix="/plans", tags=["plans"], dependencies=[Depends(get_current_user)])


class PlanRequest(BaseModel):
	goal: str
	level: str = "beginner"
	weekly_hours: int = 10
	deadline: date | None = None


@router.post("/")
async def create_plan(
	body: PlanRequest,
	current_user: dict = Depends(get_current_user),
) -> dict:
	_ = current_user
	result = await roadmap_agent.generate(
		goal=body.goal,
		level=body.level,
		weekly_hours=body.weekly_hours,
		deadline=body.deadline,
	)
	# TODO: save to DB (Sprint 3 continuation)
	return result


@router.get("/current")
async def get_current_plan() -> dict | None:
	# Placeholder until DB persistence is connected.
	return None


@router.get("/current/today", response_model=DailyPlan)
async def get_today_plan(
	current_user: dict = Depends(get_current_user),
) -> DailyPlan:
	_ = current_user
	# Stub stage; replace with real stage lookup from DB in the next step.
	mock_stage = PlanStage(
		id="mock",
		plan_id="mock",
		week_number=1,
		title="Python fundamentals",
		deliverable="Write the first script",
		status="in_progress",
		order_index=0,
	)
	plan = await daily_coach_agent.generate_plan(
		stage=mock_stage,
		available_hours=2.0,
	)
	return plan


@router.get("/{plan_id}", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_plan(plan_id: int) -> dict[str, str]:
	_ = plan_id
	return {"detail": "not implemented"}


@router.post("/{plan_id}/recalculate", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def recalculate_plan(plan_id: int) -> dict[str, str]:
	_ = plan_id
	return {"detail": "not implemented"}


@router.get("/{plan_id}/today", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_today_blocks(plan_id: int) -> dict[str, str]:
	_ = plan_id
	return {"detail": "not implemented"}
