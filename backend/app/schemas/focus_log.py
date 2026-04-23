from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FocusSessionStart(BaseModel):
    topic: str
    stage_id: Optional[UUID] = None


class FocusSessionEnd(BaseModel):
    session_id: UUID
    difficulty: int = Field(ge=1, le=5)


class FocusSessionRead(BaseModel):
    id: UUID
    user_id: UUID
    stage_id: Optional[UUID]
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: Optional[int]
    topic: str
    difficulty: Optional[int]
    completed: bool

    model_config = ConfigDict(from_attributes=True)
