from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlanStageBase(BaseModel):
    plan_id: UUID
    week_number: int
    title: str
    deliverable: str
    status: str = "pending"
    order_index: int
    start_date: date | None = None
    end_date: date | None = None
    completed_at: datetime | None = None


class PlanStageCreate(PlanStageBase):
    pass


class PlanStageUpdate(PlanStageBase):
    plan_id: Optional[UUID] = None
    week_number: Optional[int] = None
    title: Optional[str] = None
    deliverable: Optional[str] = None
    status: Optional[str] = None
    order_index: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PlanStageRead(PlanStageBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
