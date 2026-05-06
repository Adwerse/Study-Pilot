import logging
from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database import get_db
from app.repositories.focus_repository import FocusRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.user_repository import UserRepository
from app.schemas.analytics import AnalyticsReportResponse
from app.services.analytics_agent import analytics_agent
from app.services.analytics_metrics_service import (
    AnalyticsMetricsResult,
    AnalyticsMetricsService,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


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
        raise HTTPException(
            status_code=422,
            detail="Invalid timezone",
        )


def build_metrics_service(db: AsyncSession) -> AnalyticsMetricsService:
    return AnalyticsMetricsService(
        focus_repo=FocusRepository(db),
        plan_repo=PlanRepository(db),
    )


def build_response(
    result: AnalyticsMetricsResult, summary: str, recommendations: list[str]
) -> AnalyticsReportResponse:
    return AnalyticsReportResponse(
        period=result.period,
        metrics=result.metrics,
        daily_breakdown=result.daily_breakdown,
        summary=summary,
        recommendations=recommendations,
        data_quality=result.data_quality,
    )


def legacy_best_hour(result: AnalyticsMetricsResult) -> int | None:
    if not result.metrics.best_focus_hours:
        return None
    return int(result.metrics.best_focus_hours[0].split(":", maxsplit=1)[0])


@router.get("/daily", response_model=AnalyticsReportResponse)
async def get_daily_report(
    report_date: date | None = Query(default=None, alias="date"),
    timezone_name: str | None = Query(default=None, alias="timezone"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsReportResponse:
    user_timezone = resolve_timezone(timezone_name)
    try:
        user_id = await resolve_user_id(current_user, db)
        result = await build_metrics_service(db).build_daily_report(
            user_id=user_id,
            report_date=report_date,
            user_timezone=user_timezone,
        )
    except SQLAlchemyError:
        logger.exception("Failed to build daily analytics report")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics data is temporarily unavailable",
        )

    narrative = await analytics_agent.generate_report(
        period=result.period,
        metrics=result.metrics,
        daily_breakdown=result.daily_breakdown,
        data_quality=result.data_quality,
    )
    return build_response(result, narrative.summary, narrative.recommendations)


@router.get("/weekly", response_model=AnalyticsReportResponse)
async def get_weekly_report(
    week_start: date | None = None,
    timezone_name: str | None = Query(default=None, alias="timezone"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsReportResponse:
    user_timezone = resolve_timezone(timezone_name)
    try:
        user_id = await resolve_user_id(current_user, db)
        result = await build_metrics_service(db).build_weekly_report(
            user_id=user_id,
            week_start=week_start,
            user_timezone=user_timezone,
        )
    except SQLAlchemyError:
        logger.exception("Failed to build weekly analytics report")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics data is temporarily unavailable",
        )

    narrative = await analytics_agent.generate_report(
        period=result.period,
        metrics=result.metrics,
        daily_breakdown=result.daily_breakdown,
        data_quality=result.data_quality,
    )
    return build_response(result, narrative.summary, narrative.recommendations)


@router.get("/today")
async def get_today_report(
    report_date: date | None = Query(default=None, alias="date"),
    timezone_name: str | None = Query(default=None, alias="timezone"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    user_timezone = resolve_timezone(timezone_name)
    local_date = report_date or datetime.now(user_timezone).date()
    try:
        user_id = await resolve_user_id(current_user, db)
        result = await build_metrics_service(db).build_daily_report(
            user_id=user_id,
            report_date=local_date,
            user_timezone=user_timezone,
        )
    except SQLAlchemyError:
        logger.exception("Failed to build legacy daily analytics report")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics data is temporarily unavailable",
        )

    return {
        "date": local_date.isoformat(),
        "sessions_count": result.metrics.sessions_count,
        "total_minutes": result.metrics.total_focus_minutes,
        "completion_rate": result.metrics.completion_rate,
        "streak_days": result.metrics.streak_days,
        "best_hour": legacy_best_hour(result),
    }


@router.get("/week")
async def get_week_report(
    week_start: date | None = None,
    timezone_name: str | None = Query(default=None, alias="timezone"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, object]]:
    user_timezone = resolve_timezone(timezone_name)
    try:
        user_id = await resolve_user_id(current_user, db)
        result = await build_metrics_service(db).build_weekly_report(
            user_id=user_id,
            week_start=week_start,
            user_timezone=user_timezone,
        )
    except SQLAlchemyError:
        logger.exception("Failed to build legacy weekly analytics report")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics data is temporarily unavailable",
        )

    return [
        {
            "date": item.date.isoformat(),
            "sessions_count": item.sessions_count,
            "total_minutes": item.focus_minutes,
            "completion_rate": item.completion_rate,
            "streak_days": result.metrics.streak_days,
            "best_hour": legacy_best_hour(result),
        }
        for item in result.daily_breakdown or []
    ]


@router.get("/streak")
async def get_streak(
    timezone_name: str | None = Query(default=None, alias="timezone"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    user_timezone = resolve_timezone(timezone_name)
    try:
        user_id = await resolve_user_id(current_user, db)
        result = await build_metrics_service(db).build_daily_report(
            user_id=user_id,
            report_date=datetime.now(user_timezone).date(),
            user_timezone=user_timezone,
        )
    except SQLAlchemyError:
        logger.exception("Failed to build analytics streak")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics data is temporarily unavailable",
        )

    return {"streak_days": result.metrics.streak_days}
