from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.plan import Plan, PlanStage


class PlanRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: UUID, title: str, stages_data: list[dict]) -> Plan:
        plan = Plan(user_id=user_id, title=title, status="active")
        self.db.add(plan)
        await self.db.flush()

        for index, stage_data in enumerate(stages_data):
            stage = PlanStage(
                plan_id=plan.id,
                week_number=stage_data["week_number"],
                title=stage_data["title"],
                deliverable=stage_data["deliverable"],
                status="in_progress" if index == 0 else "pending",
                order_index=index,
            )
            self.db.add(stage)

        await self.db.commit()
        await self.db.refresh(plan)
        loaded_plan = await self.get_by_id(plan.id)
        return loaded_plan if loaded_plan is not None else plan

    async def get_by_id(self, plan_id: UUID) -> Plan | None:
        result = await self.db.execute(
            select(Plan).options(selectinload(Plan.stages)).where(Plan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def get_active_by_user(self, user_id: UUID) -> Plan | None:
        result = await self.db.execute(
            select(Plan)
            .options(selectinload(Plan.stages))
            .where(Plan.user_id == user_id, Plan.status == "active")
            .order_by(Plan.generated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_current_stage(self, plan_id: UUID) -> PlanStage | None:
        result = await self.db.execute(
            select(PlanStage)
            .where(PlanStage.plan_id == plan_id, PlanStage.status == "in_progress")
            .order_by(PlanStage.order_index)
            .limit(1)
        )
        stage = result.scalar_one_or_none()

        if not stage:
            result = await self.db.execute(
                select(PlanStage)
                .where(PlanStage.plan_id == plan_id, PlanStage.status == "pending")
                .order_by(PlanStage.order_index)
                .limit(1)
            )
            stage = result.scalar_one_or_none()

        return stage

    async def update_stage_status(self, stage_id: UUID, status: str) -> None:
        await self.db.execute(update(PlanStage).where(PlanStage.id == stage_id).values(status=status))
        await self.db.commit()

    async def mark_adapted(self, plan_id: UUID) -> None:
        await self.db.execute(
            update(Plan).where(Plan.id == plan_id).values(adapted_at=datetime.now(timezone.utc))
        )
        await self.db.commit()

    async def delete_stages(self, plan_id: UUID) -> None:
        from sqlalchemy import delete

        await self.db.execute(delete(PlanStage).where(PlanStage.plan_id == plan_id))
        await self.db.commit()
