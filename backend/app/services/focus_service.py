from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.models.focus_log import FocusLog
from app.repositories.focus_repository import FocusRepository
from app.schemas.focus_log import (
    FocusHistoryResponse,
    FocusSessionEnd,
    FocusSessionStart,
)


class FocusServiceError(Exception):
    status_code = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class FocusNotFoundError(FocusServiceError):
    status_code = 404


class FocusConflictError(FocusServiceError):
    status_code = 409


class FocusService:
    def __init__(self, repo: FocusRepository):
        self.repo = repo

    async def start_session(self, user_id: UUID, body: FocusSessionStart) -> FocusLog:
        active = await self.repo.get_active_session(user_id)
        if active:
            raise FocusConflictError("User already has an active focus session")

        plan_id, plan_stage_id = await self._resolve_plan_refs(
            user_id=user_id,
            plan_id=body.plan_id,
            plan_stage_id=body.plan_stage_id,
        )

        try:
            return await self.repo.create_session(
                user_id=user_id,
                topic=body.topic,
                plan_id=plan_id,
                plan_stage_id=plan_stage_id,
                planned_duration_minutes=body.planned_duration_minutes,
            )
        except IntegrityError as exc:
            await self.repo.db.rollback()
            raise FocusConflictError(
                "User already has an active focus session"
            ) from exc

    async def end_session(self, user_id: UUID, body: FocusSessionEnd) -> FocusLog:
        if body.session_id is not None:
            session = await self.repo.get_by_id(body.session_id, user_id=user_id)
            if not session:
                raise FocusNotFoundError("Focus session not found")
        else:
            session = await self.repo.get_active_session(user_id)
            if not session:
                raise FocusNotFoundError("Active focus session not found")

        if session.status != "active":
            raise FocusConflictError("Focus session is already ended")

        ended_at = datetime.now(timezone.utc)
        started_at = session.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        actual_duration_seconds = max(0, int((ended_at - started_at).total_seconds()))

        notes = body.notes.strip() if isinstance(body.notes, str) else body.notes
        if notes == "":
            notes = None

        return await self.repo.finish_session(
            session=session,
            status=body.status,
            ended_at=ended_at,
            actual_duration_seconds=actual_duration_seconds,
            difficulty=body.difficulty,
            notes=notes,
        )

    async def get_history(
        self,
        user_id: UUID,
        session_date: date | None,
        limit: int,
        offset: int,
        status: str | None,
    ) -> FocusHistoryResponse:
        items, total = await self.repo.get_history(
            user_id=user_id,
            session_date=session_date,
            limit=limit,
            offset=offset,
            status=status,
        )
        return FocusHistoryResponse(
            items=items, total=total, limit=limit, offset=offset
        )

    async def _resolve_plan_refs(
        self,
        user_id: UUID,
        plan_id: UUID | None,
        plan_stage_id: UUID | None,
    ) -> tuple[UUID | None, UUID | None]:
        if plan_stage_id is not None:
            stage = await self.repo.get_owned_stage(plan_stage_id, user_id)
            if not stage:
                raise FocusNotFoundError("Plan stage not found")
            if plan_id is not None and stage.plan_id != plan_id:
                raise FocusNotFoundError("Plan stage not found")
            return stage.plan_id, stage.id

        if plan_id is not None:
            plan = await self.repo.get_owned_plan(plan_id, user_id)
            if not plan:
                raise FocusNotFoundError("Plan not found")

        return plan_id, plan_stage_id
