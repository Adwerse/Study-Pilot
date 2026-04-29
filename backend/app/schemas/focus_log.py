from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FocusSessionStart(BaseModel):
    topic: str | None = Field(default=None, max_length=255)
    plan_id: UUID | None = None
    plan_stage_id: UUID | None = None
    stage_id: UUID | None = Field(
        default=None, description="Deprecated alias for plan_stage_id"
    )
    planned_duration_minutes: int | None = Field(default=25, gt=0, le=180)

    @model_validator(mode="after")
    def normalize_legacy_stage_id(self) -> "FocusSessionStart":
        if (
            self.stage_id is not None
            and self.plan_stage_id is not None
            and self.stage_id != self.plan_stage_id
        ):
            raise ValueError("stage_id and plan_stage_id must reference the same stage")
        if self.plan_stage_id is None:
            self.plan_stage_id = self.stage_id
        if isinstance(self.topic, str):
            self.topic = self.topic.strip() or None
        return self


class FocusSessionEnd(BaseModel):
    session_id: UUID | None = None
    status: Literal["completed", "cancelled"] = "completed"
    difficulty: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None


class FocusSessionRead(BaseModel):
    id: UUID
    user_id: UUID
    plan_id: UUID | None
    plan_stage_id: UUID | None
    stage_id: UUID | None
    status: Literal["active", "completed", "cancelled"]
    started_at: datetime
    ended_at: datetime | None
    planned_duration_minutes: int | None
    actual_duration_seconds: int | None
    duration_minutes: int | None
    topic: str | None
    difficulty: int | None
    notes: str | None
    completed: bool
    created_at: datetime | None
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class FocusHistoryResponse(BaseModel):
    items: list[FocusSessionRead]
    total: int
    limit: int
    offset: int
