from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.focus import focus_agent
from app.api.dependencies import get_current_user
from app.database import get_db
from app.repositories.focus_repository import FocusRepository
from app.repositories.user_repository import UserRepository
from app.schemas.focus_log import FocusSessionEnd, FocusSessionRead, FocusSessionStart


router = APIRouter(prefix="/focus", tags=["focus"])


async def resolve_user_id(current_user: dict, db: AsyncSession) -> UUID:
    """Resolve UUID пользователя из telegram_id через БД."""
    user_repo = UserRepository(db)
    user = await user_repo.get_or_create_by_telegram_id(
        telegram_id=int(current_user["id"]),
        username=current_user.get("username"),
        first_name=current_user.get("first_name"),
    )
    return user.id


@router.post("/start", response_model=FocusSessionRead)
async def start_session(
    body: FocusSessionStart,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await resolve_user_id(current_user, db)
    repo = FocusRepository(db)

    active = await repo.get_active_session(user_id)
    if active:
        raise HTTPException(409, "Активная сессия уже существует. Завершите её перед стартом.")

    session = await repo.start_session(
        user_id=user_id,
        topic=body.topic,
        stage_id=body.stage_id,
    )

    # TODO: bot/notifications.py -> send_focus_reminder(current_user["id"], msg)
    # msg = focus_agent.format_start_message(session)
    # Подключить в Спринте 4 после интеграции бота с бэком
    _ = focus_agent

    return session


@router.post("/end", response_model=FocusSessionRead)
async def end_session(
    body: FocusSessionEnd,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await resolve_user_id(current_user, db)
    repo = FocusRepository(db)

    session = await repo.end_session(
        session_id=body.session_id,
        difficulty=body.difficulty,
        user_id=user_id,
    )
    if not session:
        raise HTTPException(404, "Сессия не найдена")

    today_sessions = await repo.get_today_sessions(user_id)

    # TODO: bot/notifications.py -> send_focus_reminder(current_user["id"], msg)
    # msg = focus_agent.format_end_message(session, len(today_sessions))
    # Подключить в Спринте 4 после интеграции бота с бэком
    _ = today_sessions

    return session


@router.get("/active", response_model=FocusSessionRead | None)
async def get_active_session(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await resolve_user_id(current_user, db)
    repo = FocusRepository(db)
    return await repo.get_active_session(user_id)


@router.get("/history", response_model=list[FocusSessionRead])
async def get_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = await resolve_user_id(current_user, db)
    repo = FocusRepository(db)
    return await repo.get_history(user_id)
