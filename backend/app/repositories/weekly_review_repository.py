from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weekly_review import WeeklyReview


class WeeklyReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        user_id: UUID,
        plan_id: UUID,
        period_start: datetime,
        period_end: datetime,
        timezone_name: str,
        summary: str,
        insights: list[str],
        risks: list[str],
        recommendations: list[str],
        metrics: dict,
        proposed_changes: list[dict],
        status: str = "draft",
    ) -> WeeklyReview:
        review = WeeklyReview(
            user_id=user_id,
            plan_id=plan_id,
            period_start=period_start,
            period_end=period_end,
            timezone=timezone_name,
            status=status,
            summary=summary,
            insights=insights,
            risks=risks,
            recommendations=recommendations,
            metrics=metrics,
            proposed_changes=proposed_changes,
        )
        self.db.add(review)
        await self.db.flush()
        return review

    async def get_by_id_for_user(
        self,
        review_id: UUID,
        user_id: UUID,
    ) -> WeeklyReview | None:
        result = await self.db.execute(
            select(WeeklyReview).where(
                WeeklyReview.id == review_id,
                WeeklyReview.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_history(
        self,
        *,
        user_id: UUID,
        plan_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[WeeklyReview], int]:
        filters = [WeeklyReview.user_id == user_id]
        if plan_id is not None:
            filters.append(WeeklyReview.plan_id == plan_id)

        total_result = await self.db.execute(
            select(func.count()).select_from(WeeklyReview).where(*filters)
        )
        total = int(total_result.scalar_one())

        items_result = await self.db.execute(
            select(WeeklyReview)
            .where(*filters)
            .order_by(WeeklyReview.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(items_result.scalars().all()), total
