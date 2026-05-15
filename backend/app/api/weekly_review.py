import logging
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.weekly_review import (
    ApplyWeeklyReviewResponse,
    WeeklyReviewGenerateRequest,
    WeeklyReviewHistoryResponse,
    WeeklyReviewResponse,
)
from app.services.weekly_review_service import (
    WeeklyReviewServiceError,
    build_weekly_review_service,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weekly-review", tags=["weekly-review"])


async def resolve_user_id(current_user: dict, db: AsyncSession) -> UUID:
    telegram_id = current_user.get("id")
    if telegram_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram user id missing",
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_or_create_by_telegram_id(
        telegram_id=int(telegram_id),
        username=current_user.get("username"),
        first_name=current_user.get("first_name"),
    )
    return user.id


def resolve_timezone(timezone_name: str | None) -> ZoneInfo:
    name = (timezone_name or "UTC").strip() or "UTC"
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        raise HTTPException(status_code=422, detail="Invalid timezone")


def raise_service_error(error: WeeklyReviewServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post("/generate", response_model=WeeklyReviewResponse)
async def generate_weekly_review(
    body: WeeklyReviewGenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeeklyReviewResponse:
    user_timezone = resolve_timezone(body.timezone or current_user.get("timezone"))
    try:
        user_id = await resolve_user_id(current_user, db)
        return await build_weekly_review_service(db).generate_review(
            user_id=user_id,
            plan_id=body.plan_id,
            week_start=body.week_start,
            user_timezone=user_timezone,
            apply_changes=body.apply_changes,
        )
    except WeeklyReviewServiceError as error:
        raise_service_error(error)
    except (SQLAlchemyError, OSError):
        logger.exception("Failed to generate weekly review")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weekly review data is temporarily unavailable",
        )


@router.post("/{review_id}/apply", response_model=ApplyWeeklyReviewResponse)
async def apply_weekly_review(
    review_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApplyWeeklyReviewResponse:
    try:
        user_id = await resolve_user_id(current_user, db)
        return await build_weekly_review_service(db).apply_review(
            user_id=user_id,
            review_id=review_id,
        )
    except WeeklyReviewServiceError as error:
        raise_service_error(error)
    except (SQLAlchemyError, OSError):
        logger.exception("Failed to apply weekly review")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weekly review data is temporarily unavailable",
        )


@router.get("/history", response_model=WeeklyReviewHistoryResponse)
async def get_weekly_review_history(
    plan_id: UUID | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeeklyReviewHistoryResponse:
    try:
        user_id = await resolve_user_id(current_user, db)
        return await build_weekly_review_service(db).list_history(
            user_id=user_id,
            plan_id=plan_id,
            limit=limit,
            offset=offset,
        )
    except WeeklyReviewServiceError as error:
        raise_service_error(error)
    except (SQLAlchemyError, OSError):
        logger.exception("Failed to list weekly review history")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Weekly review data is temporarily unavailable",
        )
