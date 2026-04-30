from datetime import date
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.daily_coach import daily_coach_agent
from app.agents.roadmap import roadmap_agent
from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.plan import PlanStage as PlanStageModel
from app.repositories.plan_repository import PlanRepository
from app.repositories.runtime_store import (
    get_current_stage as get_runtime_current_stage,
    get_plan as get_saved_plan,
    get_today_focus_summary,
    get_user_key,
    save_plan,
)
from app.schemas.focus_block import DailyPlan
from app.schemas.plan import PlanRead, PlanStage, PlanStageStatusUpdate


router = APIRouter(prefix="/plans", tags=["plans"])


class PlanRequest(BaseModel):
    goal: str
    level: str = "beginner"
    weekly_hours: int = 10
    deadline: date | None = None


async def resolve_user_id(db: AsyncSession, current_user: dict) -> UUID:
    telegram_id = current_user.get("id")
    if telegram_id is None:
        raise HTTPException(status_code=401, detail="Telegram user id missing")

    result = await db.execute(
        text(
            """
            INSERT INTO users (id, telegram_id, username)
            VALUES (:id, :telegram_id, :username)
            ON CONFLICT (telegram_id)
            DO UPDATE SET username = COALESCE(EXCLUDED.username, users.username)
            RETURNING id
            """
        ),
        {
            "id": uuid4(),
            "telegram_id": int(telegram_id),
            "username": current_user.get("username"),
        },
    )
    return result.scalar_one()


async def get_owned_plan_or_404(repo: PlanRepository, plan_id: UUID, user_id: UUID):
    plan = await repo.get_by_id(plan_id)
    if not plan or plan.user_id != user_id:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


def build_stage_payload(stage: PlanStageModel) -> PlanStage:
    return PlanStage(
        id=str(stage.id),
        plan_id=str(stage.plan_id),
        week_number=stage.week_number,
        title=stage.title,
        deliverable=stage.deliverable,
        status=stage.status,
        order_index=stage.order_index,
    )


async def generate_daily_plan_for_stage(stage: PlanStage, current_user: dict) -> DailyPlan:
    completed_today, minutes_today, topics_today = get_today_focus_summary(get_user_key(current_user), date.today())
    available_hours = max(0.5, 2.0 - (minutes_today / 60))

    return await daily_coach_agent.generate_plan(
        stage=stage,
        completed_today=completed_today,
        minutes_today=minutes_today,
        topics_today=topics_today,
        available_hours=available_hours,
    )


@router.post("", response_model=PlanRead, include_in_schema=False)
@router.post("/", response_model=PlanRead)
async def create_plan(
    body: PlanRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_key = get_user_key(current_user)
    repo = PlanRepository(db)
    llm_result = await roadmap_agent.generate(
        goal=body.goal,
        level=body.level,
        weekly_hours=body.weekly_hours,
        deadline=body.deadline,
    )

    try:
        user_id = await resolve_user_id(db, current_user)
        return await repo.create(
            user_id=user_id,
            title=llm_result["title"],
            stages_data=llm_result["stages"],
        )
    except (SQLAlchemyError, OSError):
        return save_plan(user_key, llm_result)


@router.get("/current", response_model=PlanRead)
async def get_current_plan(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_key = get_user_key(current_user)
    repo = PlanRepository(db)

    try:
        user_id = await resolve_user_id(db, current_user)
        plan = await repo.get_active_by_user(user_id)
        if plan:
            return plan
    except (SQLAlchemyError, OSError):
        pass

    saved_plan = get_saved_plan(user_key)
    if saved_plan:
        return saved_plan

    raise HTTPException(status_code=404, detail="Active plan not found")


@router.get("/current/today", response_model=DailyPlan)
async def get_today(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_key = get_user_key(current_user)
    repo = PlanRepository(db)

    try:
        user_id = await resolve_user_id(db, current_user)
        plan = await repo.get_active_by_user(user_id)
        if plan:
            stage = await repo.get_current_stage(plan.id)
            if stage:
                return await generate_daily_plan_for_stage(build_stage_payload(stage), current_user)
    except (SQLAlchemyError, OSError):
        pass

    runtime_stage = get_runtime_current_stage(user_key)
    if runtime_stage:
        return await generate_daily_plan_for_stage(PlanStage.model_validate(runtime_stage), current_user)

    raise HTTPException(status_code=404, detail="Current stage not found")


@router.get("/{plan_id}", response_model=PlanRead)
async def get_plan(
    plan_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = PlanRepository(db)
    user_id = await resolve_user_id(db, current_user)
    return await get_owned_plan_or_404(repo, plan_id, user_id)


@router.post("/{plan_id}/recalculate", response_model=PlanRead)
async def recalculate_plan(
    plan_id: UUID,
    body: PlanRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = PlanRepository(db)
    user_id = await resolve_user_id(db, current_user)
    await get_owned_plan_or_404(repo, plan_id, user_id)

    llm_result = await roadmap_agent.generate(
        goal=body.goal,
        level=body.level,
        weekly_hours=body.weekly_hours,
        deadline=body.deadline,
    )

    await repo.delete_stages(plan_id)

    for index, stage_data in enumerate(llm_result["stages"]):
        db.add(
            PlanStageModel(
                plan_id=plan_id,
                week_number=stage_data["week_number"],
                title=stage_data["title"],
                deliverable=stage_data["deliverable"],
                status="in_progress" if index == 0 else "pending",
                order_index=index,
            )
        )

    await repo.mark_adapted(plan_id)
    await db.commit()
    updated_plan = await repo.get_by_id(plan_id)
    if not updated_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return updated_plan


@router.patch("/stages/{stage_id}")
async def update_stage_status(
    stage_id: UUID,
    body: PlanStageStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ = current_user
    repo = PlanRepository(db)
    await repo.update_stage_status(stage_id, body.status)
    return {"ok": True}
