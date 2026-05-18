from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.weekly_digest import WeeklyDigestDelivery


class WeeklyDigestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_due_candidates(self) -> list[User]:
        result = await self.db.execute(
            select(User)
            .where(
                User.telegram_id.is_not(None),
                User.notifications_enabled.is_(True),
                User.weekly_digest_enabled.is_(True),
            )
            .order_by(User.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_delivery(
        self,
        *,
        user_id: UUID,
        week_start: datetime,
        week_end: datetime,
    ) -> WeeklyDigestDelivery | None:
        result = await self.db.execute(
            select(WeeklyDigestDelivery).where(
                WeeklyDigestDelivery.user_id == user_id,
                WeeklyDigestDelivery.week_start == week_start,
                WeeklyDigestDelivery.week_end == week_end,
            )
        )
        return result.scalar_one_or_none()

    async def get_delivery_for_update(
        self,
        *,
        user_id: UUID,
        week_start: datetime,
        week_end: datetime,
        skip_locked: bool = True,
    ) -> WeeklyDigestDelivery | None:
        result = await self.db.execute(
            select(WeeklyDigestDelivery)
            .where(
                WeeklyDigestDelivery.user_id == user_id,
                WeeklyDigestDelivery.week_start == week_start,
                WeeklyDigestDelivery.week_end == week_end,
            )
            .with_for_update(skip_locked=skip_locked)
        )
        return result.scalar_one_or_none()

    async def create_pending_delivery(
        self,
        *,
        user_id: UUID,
        telegram_id: int,
        week_start: datetime,
        week_end: datetime,
        timezone_name: str,
    ) -> WeeklyDigestDelivery | None:
        insert_stmt = (
            insert(WeeklyDigestDelivery)
            .values(
                user_id=user_id,
                telegram_id=telegram_id,
                week_start=week_start,
                week_end=week_end,
                timezone=timezone_name,
                status="pending",
            )
            .on_conflict_do_nothing(
                index_elements=[
                    WeeklyDigestDelivery.user_id,
                    WeeklyDigestDelivery.week_start,
                    WeeklyDigestDelivery.week_end,
                ]
            )
            .returning(WeeklyDigestDelivery.id)
        )
        result = await self.db.execute(insert_stmt)
        delivery_id = result.scalar_one_or_none()
        if delivery_id is None:
            return None
        return await self.db.get(WeeklyDigestDelivery, delivery_id)

    async def claim_or_create_pending_delivery(
        self,
        *,
        user_id: UUID,
        telegram_id: int,
        week_start: datetime,
        week_end: datetime,
        timezone_name: str,
        retry_failed: bool = False,
    ) -> WeeklyDigestDelivery | None:
        delivery = await self.get_delivery_for_update(
            user_id=user_id,
            week_start=week_start,
            week_end=week_end,
            skip_locked=True,
        )
        if delivery is None:
            existing = await self.get_delivery(
                user_id=user_id,
                week_start=week_start,
                week_end=week_end,
            )
            if existing is not None:
                return None

            delivery = await self.create_pending_delivery(
                user_id=user_id,
                telegram_id=telegram_id,
                week_start=week_start,
                week_end=week_end,
                timezone_name=timezone_name,
            )
            if delivery is None:
                delivery = await self.get_delivery_for_update(
                    user_id=user_id,
                    week_start=week_start,
                    week_end=week_end,
                    skip_locked=True,
                )

        if delivery is not None and delivery.status == "failed" and retry_failed:
            delivery.status = "pending"
            delivery.telegram_id = telegram_id
            delivery.timezone = timezone_name
            delivery.error_message = None
            delivery.sent_at = None
            delivery.telegram_message_id = None
            await self.db.flush()

        return delivery

    async def mark_sent(
        self,
        delivery: WeeklyDigestDelivery,
        *,
        message_text: str,
        telegram_message_id: int | None,
        sent_at: datetime | None = None,
    ) -> WeeklyDigestDelivery:
        delivery.status = "sent"
        delivery.message_text = message_text
        delivery.telegram_message_id = telegram_message_id
        delivery.error_message = None
        delivery.sent_at = sent_at or datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(delivery)
        return delivery

    async def mark_failed(
        self,
        delivery: WeeklyDigestDelivery,
        error_message: str,
    ) -> WeeklyDigestDelivery:
        delivery.status = "failed"
        delivery.error_message = error_message[:500]
        await self.db.commit()
        await self.db.refresh(delivery)
        return delivery

    async def mark_skipped(
        self,
        delivery: WeeklyDigestDelivery,
        reason: str | None = None,
    ) -> WeeklyDigestDelivery:
        delivery.status = "skipped"
        delivery.error_message = reason[:500] if reason else None
        await self.db.commit()
        await self.db.refresh(delivery)
        return delivery
