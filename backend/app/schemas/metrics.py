from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MetricsBase(BaseModel):
    user_id: UUID
    date: date
    sessions_count: int = 0
    total_minutes: int = 0
    completion_rate: float = 0
    streak_days: int = 0
    best_hour: Optional[int] = None


class MetricsCreate(MetricsBase):
    pass


class MetricsUpdate(MetricsBase):
    user_id: Optional[UUID] = None
    date: Optional[date] = None
    sessions_count: Optional[int] = None
    total_minutes: Optional[int] = None
    completion_rate: Optional[float] = None
    streak_days: Optional[int] = None
    best_hour: Optional[int] = None


class MetricsRead(MetricsBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
