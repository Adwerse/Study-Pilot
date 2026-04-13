from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user


router = APIRouter(prefix="/analytics", tags=["analytics"], dependencies=[Depends(get_current_user)])


@router.get("/today", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_today_report() -> dict[str, str]:
	return {"detail": "not implemented"}


@router.get("/week", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_week_report() -> dict[str, str]:
	return {"detail": "not implemented"}


@router.get("/streak", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_streak() -> dict[str, str]:
	return {"detail": "not implemented"}
