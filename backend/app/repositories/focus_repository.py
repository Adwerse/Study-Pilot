from collections.abc import Sequence
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.focus_log import FocusLog
from app.models.plan import Plan, PlanStage


class FocusRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        user_id: UUID,
        topic: str | None = None,
        plan_id: UUID | None = None,
        plan_stage_id: UUID | None = None,
        planned_duration_minutes: int | None = None,
    ) -> FocusLog:
        session = FocusLog(
            user_id=user_id,
            topic=topic,
            plan_id=plan_id,
            plan_stage_id=plan_stage_id,
            planned_duration_minutes=planned_duration_minutes,
            status="active",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def start_session(
        self,
        user_id: UUID,
        topic: str | None = None,
        stage_id: UUID | None = None,
    ) -> FocusLog:
        return await self.create_session(
            user_id=user_id,
            topic=topic,
            plan_stage_id=stage_id,
            planned_duration_minutes=25,
        )

    async def get_by_id(
        self, session_id: UUID, user_id: UUID | None = None
    ) -> FocusLog | None:
        query = select(FocusLog).where(FocusLog.id == session_id)
        if user_id is not None:
            query = query.where(FocusLog.user_id == user_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_session(self, user_id: UUID) -> FocusLog | None:
        result = await self.db.execute(
            select(FocusLog)
            .where(
                FocusLog.user_id == user_id,
                FocusLog.status == "active",
            )
            .order_by(FocusLog.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def finish_session(
        self,
        session: FocusLog,
        status: str,
        ended_at: datetime,
        actual_duration_seconds: int,
        difficulty: int | None = None,
        notes: str | None = None,
    ) -> FocusLog:
        session.status = status
        session.ended_at = ended_at
        session.actual_duration_seconds = actual_duration_seconds
        session.difficulty = difficulty
        session.notes = notes
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def end_session(
        self,
        session_id: UUID,
        difficulty: int | None = None,
        user_id: UUID | None = None,
    ) -> FocusLog | None:
        session = await self.get_by_id(session_id, user_id)
        if not session:
            return None

        ended_at = datetime.now(timezone.utc)
        started_at = session.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        actual_duration_seconds = max(0, int((ended_at - started_at).total_seconds()))

        return await self.finish_session(
            session=session,
            status="completed",
            ended_at=ended_at,
            actual_duration_seconds=actual_duration_seconds,
            difficulty=difficulty,
        )

    async def get_history(
        self,
        user_id: UUID,
        session_date: date | None = None,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
    ) -> tuple[list[FocusLog], int]:
        filters = [FocusLog.user_id == user_id]

        if status is not None:
            filters.append(FocusLog.status == status)

        if session_date is not None:
            day_start = datetime.combine(session_date, time.min, tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)
            filters.extend(
                [FocusLog.started_at >= day_start, FocusLog.started_at < day_end]
            )

        total_result = await self.db.execute(
            select(func.count()).select_from(FocusLog).where(*filters)
        )
        total = int(total_result.scalar_one())

        items_result = await self.db.execute(
            select(FocusLog)
            .where(*filters)
            .order_by(FocusLog.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(items_result.scalars().all()), total

    async def get_today_sessions(self, user_id: UUID) -> list[FocusLog]:
        today = datetime.now(timezone.utc).date()
        items, _ = await self.get_history(
            user_id=user_id, session_date=today, limit=1000, status="completed"
        )
        return items

    async def list_sessions_between(
        self,
        user_id: UUID,
        start_utc: datetime,
        end_utc: datetime,
        statuses: Sequence[str] | None = None,
    ) -> list[FocusLog]:
        query = select(FocusLog).where(
            FocusLog.user_id == user_id,
            FocusLog.started_at >= start_utc,
            FocusLog.started_at < end_utc,
        )
        if statuses is not None:
            query = query.where(FocusLog.status.in_(list(statuses)))

        result = await self.db.execute(query.order_by(FocusLog.started_at.asc()))
        return list(result.scalars().all())

    async def list_completed_sessions_until(
        self,
        user_id: UUID,
        end_utc: datetime,
    ) -> list[FocusLog]:
        result = await self.db.execute(
            select(FocusLog)
            .where(
                FocusLog.user_id == user_id,
                FocusLog.status == "completed",
                FocusLog.actual_duration_seconds > 0,
                FocusLog.started_at < end_utc,
            )
            .order_by(FocusLog.started_at.desc())
        )
        return list(result.scalars().all())

    async def get_owned_plan(self, plan_id: UUID, user_id: UUID) -> Plan | None:
        result = await self.db.execute(
            select(Plan).where(Plan.id == plan_id, Plan.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_owned_stage(self, stage_id: UUID, user_id: UUID) -> PlanStage | None:
        result = await self.db.execute(
            select(PlanStage)
            .join(Plan, PlanStage.plan_id == Plan.id)
            .where(PlanStage.id == stage_id, Plan.user_id == user_id)
        )
        return result.scalar_one_or_none()
