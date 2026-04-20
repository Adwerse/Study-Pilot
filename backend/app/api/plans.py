from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.agents.daily_coach import daily_coach_agent
from app.agents.roadmap import roadmap_agent
from app.api.dependencies import get_current_user
from app.repositories.runtime_store import (
	get_current_stage,
	get_plan as get_saved_plan,
	get_today_focus_summary,
	get_user_key,
	save_plan,
)
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
	roadmap = await roadmap_agent.generate(
		goal=body.goal,
		level=body.level,
		weekly_hours=body.weekly_hours,
		deadline=body.deadline,
	)
	user_key = get_user_key(current_user)
	return save_plan(user_key, roadmap)


@router.get("/current")
async def get_current_plan(
	current_user: dict = Depends(get_current_user),
) -> dict | None:
	user_key = get_user_key(current_user)
	return get_saved_plan(user_key)


@router.get("/current/today", response_model=DailyPlan)
async def get_today_plan(
	current_user: dict = Depends(get_current_user),
) -> DailyPlan:
	user_key = get_user_key(current_user)
	current_stage = get_current_stage(user_key)
	if not current_stage:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active plan")

	stage = PlanStage.model_validate(current_stage)
	completed_today, minutes_today, topics_today = get_today_focus_summary(user_key, date.today())
	available_hours = max(0.5, 2.0 - (minutes_today / 60))

	return await daily_coach_agent.generate_plan(
		stage=stage,
		completed_today=completed_today,
		minutes_today=minutes_today,
		topics_today=topics_today,
		available_hours=available_hours,
	)


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
