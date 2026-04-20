from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.repositories.runtime_store import (
	end_focus_session,
	get_focus_history,
	get_user_key,
	start_focus_session,
)
from app.schemas.focus_session import FocusSession


router = APIRouter(prefix="/focus", tags=["focus"], dependencies=[Depends(get_current_user)])


class FocusStartRequest(BaseModel):
	topic: str
	stage_id: str | None = None


class FocusEndRequest(BaseModel):
	session_id: str
	difficulty: int = Field(ge=1, le=5)


@router.post("/start", response_model=FocusSession)
async def start_focus(
	body: FocusStartRequest,
	current_user: dict = Depends(get_current_user),
) -> FocusSession:
	user_key = get_user_key(current_user)
	return start_focus_session(
		user_key=user_key,
		topic=body.topic,
		stage_id=body.stage_id,
	)


@router.post("/end", response_model=FocusSession)
async def end_focus(
	body: FocusEndRequest,
	current_user: dict = Depends(get_current_user),
) -> FocusSession:
	user_key = get_user_key(current_user)
	ended_session = end_focus_session(
		user_key=user_key,
		session_id=body.session_id,
		difficulty=body.difficulty,
	)
	if not ended_session:
		raise HTTPException(status_code=404, detail="Focus session not found")
	return ended_session


@router.get("/history", response_model=list[FocusSession])
async def get_focus_history_endpoint(
	current_user: dict = Depends(get_current_user),
) -> list[FocusSession]:
	user_key = get_user_key(current_user)
	return get_focus_history(user_key)
