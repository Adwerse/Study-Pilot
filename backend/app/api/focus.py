from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database import get_db
from app.repositories.focus_repository import FocusRepository
from app.repositories.user_repository import UserRepository
from app.schemas.focus_log import (
    FocusHistoryResponse,
    FocusSessionEnd,
    FocusSessionRead,
    FocusSessionStart,
)
from app.services.focus_service import FocusService, FocusServiceError


router = APIRouter(prefix="/focus", tags=["focus"])


async def resolve_user_id(current_user: dict, db: AsyncSession) -> UUID:
    telegram_id = current_user.get("id")
    if telegram_id is None:
        raise HTTPException(status_code=401, detail="Telegram user id missing")

    user_repo = UserRepository(db)
    user = await user_repo.get_or_create_by_telegram_id(
        telegram_id=int(telegram_id),
        username=current_user.get("username"),
        first_name=current_user.get("first_name"),
    )
    return user.id


def build_focus_service(db: AsyncSession) -> FocusService:
    return FocusService(FocusRepository(db))


def raise_http_error(error: FocusServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post("/start", response_model=FocusSessionRead)
async def start_session(
    body: FocusSessionStart,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await resolve_user_id(current_user, db)
    service = build_focus_service(db)

    try:
        return await service.start_session(user_id=user_id, body=body)
    except FocusServiceError as error:
        raise_http_error(error)


@router.post("/end", response_model=FocusSessionRead)
async def end_session(
    body: FocusSessionEnd,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await resolve_user_id(current_user, db)
    service = build_focus_service(db)

    try:
        return await service.end_session(user_id=user_id, body=body)
    except FocusServiceError as error:
        raise_http_error(error)


@router.get("/active", response_model=FocusSessionRead | None)
async def get_active_session(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await resolve_user_id(current_user, db)
    repo = FocusRepository(db)
    return await repo.get_active_session(user_id)


@router.get("/history", response_model=FocusHistoryResponse)
async def get_history(
    session_date: date | None = Query(default=None, alias="date"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Literal["active", "completed", "cancelled"] | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await resolve_user_id(current_user, db)
    service = build_focus_service(db)
    return await service.get_history(
        user_id=user_id,
        session_date=session_date,
        limit=limit,
        offset=offset,
        status=status,
    )
