from datetime import date

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.agents.roadmap import roadmap_agent
from app.api.dependencies import get_current_user


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


@router.get("/current", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_current_plan() -> dict[str, str]:
	return {"detail": "not implemented"}


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
