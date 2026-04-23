from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Date, cast, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.focus_log import FocusLog


class FocusRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_session(
        self,
        user_id: UUID,
        topic: str,
        stage_id: UUID | None = None,
    ) -> FocusLog:
        session = FocusLog(
            user_id=user_id,
            topic=topic,
            stage_id=stage_id,
            started_at=datetime.now(timezone.utc),
            completed=False,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def end_session(
        self,
        session_id: UUID,
        difficulty: int,
        user_id: UUID | None = None,
    ) -> FocusLog | None:
        query = select(FocusLog).where(FocusLog.id == session_id)
        if user_id is not None:
            query = query.where(FocusLog.user_id == user_id)

        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        if not session:
            return None

        ended_at = datetime.now(timezone.utc)
        duration = int((ended_at - session.started_at).total_seconds() / 60)

        update_query = update(FocusLog).where(FocusLog.id == session_id)
        if user_id is not None:
            update_query = update_query.where(FocusLog.user_id == user_id)

        await self.db.execute(
            update_query.values(
                ended_at=ended_at,
                duration_minutes=max(1, duration),
                difficulty=difficulty,
                completed=True,
            )
        )
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_active_session(self, user_id: UUID) -> FocusLog | None:
        result = await self.db.execute(
            select(FocusLog)
            .where(
                FocusLog.user_id == user_id,
                FocusLog.ended_at.is_(None),
                FocusLog.completed.is_(False),
            )
            .order_by(FocusLog.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(self, user_id: UUID, limit: int = 20) -> list[FocusLog]:
        result = await self.db.execute(
            select(FocusLog)
            .where(FocusLog.user_id == user_id)
            .order_by(FocusLog.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_today_sessions(self, user_id: UUID) -> list[FocusLog]:
        today = datetime.now(timezone.utc).date()
        result = await self.db.execute(
            select(FocusLog).where(
                FocusLog.user_id == user_id,
                FocusLog.completed.is_(True),
                cast(FocusLog.started_at, Date) == today,
            )
        )
        return list(result.scalars().all())
