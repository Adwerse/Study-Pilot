from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user


router = APIRouter(prefix="/plans", tags=["plans"], dependencies=[Depends(get_current_user)])


@router.post("", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def create_plan() -> dict[str, str]:
	return {"detail": "not implemented"}


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
