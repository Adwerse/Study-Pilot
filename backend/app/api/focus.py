from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user


router = APIRouter(prefix="/focus", tags=["focus"], dependencies=[Depends(get_current_user)])


@router.post("/start", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def start_focus() -> dict[str, str]:
	return {"detail": "not implemented"}


@router.post("/end", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def end_focus() -> dict[str, str]:
	return {"detail": "not implemented"}


@router.get("/history", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_focus_history() -> dict[str, str]:
	return {"detail": "not implemented"}
