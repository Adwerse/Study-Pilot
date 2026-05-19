from datetime import date
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.config import settings
from app.database import get_db
from app.repositories.focus_repository import FocusRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.runtime_store import (
    end_focus_session,
    get_focus_history as get_runtime_focus_history,
    get_user_key,
    start_focus_session,
)
from app.repositories.user_repository import UserRepository
from app.schemas.focus_log import (
    FocusHistoryResponse,
    FocusSessionEnd,
    FocusSessionRead,
    FocusSessionStart,
)
from app.services.focus_service import FocusService, FocusServiceError
from app.services.notification_service import NotificationService


router = APIRouter(prefix="/focus", tags=["focus"])


def should_use_runtime_fallback(error: Exception) -> bool:
    return settings.APP_ENV != "production" and isinstance(
        error, (SQLAlchemyError, OSError)
    )


def runtime_user_uuid(user_key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"user:{user_key}")


def runtime_session_payload(session, user_key: str) -> dict:
    duration_minutes = session.duration_minutes
    return {
        "id": UUID(str(session.id)),
        "user_id": runtime_user_uuid(user_key),
        "plan_id": None,
        "plan_stage_id": UUID(str(session.stage_id)) if session.stage_id else None,
        "stage_id": UUID(str(session.stage_id)) if session.stage_id else None,
        "status": "completed" if session.completed else "active",
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "planned_duration_minutes": None,
        "actual_duration_seconds": duration_minutes * 60
        if duration_minutes is not None
        else None,
        "duration_minutes": duration_minutes,
        "topic": session.topic,
        "difficulty": session.difficulty,
        "notes": None,
        "completed": session.completed,
        "created_at": None,
        "updated_at": None,
    }


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
    notification_service = NotificationService(NotificationRepository(db))
    return FocusService(FocusRepository(db), notification_service)


def raise_http_error(error: FocusServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post("/start", response_model=FocusSessionRead)
async def start_session(
    body: FocusSessionStart,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    telegram_id = current_user.get("id")
    try:
        user_id = await resolve_user_id(current_user, db)
        service = build_focus_service(db)
        return await service.start_session(
            user_id=user_id,
            body=body,
            telegram_id=telegram_id,
        )
    except FocusServiceError as error:
        raise_http_error(error)
    except Exception as error:
        if not should_use_runtime_fallback(error):
            raise
        user_key = get_user_key(current_user)
        session = start_focus_session(
            user_key=user_key,
            topic=body.topic or "",
            stage_id=str(body.plan_stage_id) if body.plan_stage_id else None,
        )
        return runtime_session_payload(session, user_key)


@router.post("/end", response_model=FocusSessionRead)
async def end_session(
    body: FocusSessionEnd,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = await resolve_user_id(current_user, db)
        service = build_focus_service(db)
        return await service.end_session(user_id=user_id, body=body)
    except FocusServiceError as error:
        raise_http_error(error)
    except Exception as error:
        if not should_use_runtime_fallback(error):
            raise
        if body.session_id is None:
            raise HTTPException(
                status_code=404, detail="Active focus session not found"
            )
        user_key = get_user_key(current_user)
        session = end_focus_session(
            user_key=user_key,
            session_id=str(body.session_id),
            difficulty=body.difficulty or 3,
        )
        if not session:
            raise HTTPException(status_code=404, detail="Focus session not found")
        return runtime_session_payload(session, user_key)


@router.get("/active", response_model=FocusSessionRead | None)
async def get_active_session(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = await resolve_user_id(current_user, db)
        repo = FocusRepository(db)
        return await repo.get_active_session(user_id)
    except Exception as error:
        if not should_use_runtime_fallback(error):
            raise
        user_key = get_user_key(current_user)
        for session in get_runtime_focus_history(user_key):
            if not session.completed:
                return runtime_session_payload(session, user_key)
        return None


@router.get("/history", response_model=FocusHistoryResponse)
async def get_history(
    session_date: date | None = Query(default=None, alias="date"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Literal["active", "completed", "cancelled"] | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = await resolve_user_id(current_user, db)
        service = build_focus_service(db)
        return await service.get_history(
            user_id=user_id,
            session_date=session_date,
            limit=limit,
            offset=offset,
            status=status,
        )
    except Exception as error:
        if not should_use_runtime_fallback(error):
            raise
        user_key = get_user_key(current_user)
        sessions = get_runtime_focus_history(user_key)
        if session_date is not None:
            sessions = [
                session
                for session in sessions
                if (session.ended_at or session.started_at).date() == session_date
            ]
        if status is not None:
            if status == "cancelled":
                sessions = []
            else:
                expected_completed = status == "completed"
                sessions = [
                    session
                    for session in sessions
                    if session.completed is expected_completed
                ]
        total = len(sessions)
        page = sessions[offset : offset + limit]
        return FocusHistoryResponse(
            items=[runtime_session_payload(session, user_key) for session in page],
            total=total,
            limit=limit,
            offset=offset,
        )
