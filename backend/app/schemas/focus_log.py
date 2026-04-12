from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FocusLogBase(BaseModel):
    user_id: UUID
    stage_id: Optional[UUID] = None
    duration_minutes: Optional[int] = None
    topic: str
    difficulty: Optional[int] = None
    completed: bool = False


class FocusLogCreate(FocusLogBase):
    started_at: datetime
    ended_at: Optional[datetime] = None


class FocusLogUpdate(FocusLogBase):
    user_id: Optional[UUID] = None
    stage_id: Optional[UUID] = None
    duration_minutes: Optional[int] = None
    topic: Optional[str] = None
    difficulty: Optional[int] = None
    completed: Optional[bool] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class FocusLogRead(FocusLogBase):
    id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)