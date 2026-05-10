from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlanBase(BaseModel):
    title: str


class PlanCreate(PlanBase):
    user_id: UUID
    status: str = "active"


class PlanUpdate(BaseModel):
    user_id: Optional[UUID] = None
    title: Optional[str] = None
    status: Optional[str] = None


class PlanStageBase(BaseModel):
    week_number: int
    title: str
    deliverable: str


class PlanStage(BaseModel):
    id: str
    plan_id: str
    week_number: int
    title: str
    deliverable: str
    status: str = "pending"
    order_index: int
    start_date: date | None = None
    end_date: date | None = None
    topics: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PlanStageRead(PlanStageBase):
    id: UUID
    plan_id: UUID
    status: str
    order_index: int
    start_date: date | None = None
    end_date: date | None = None

    model_config = ConfigDict(from_attributes=True)


class PlanRead(PlanBase):
    id: UUID
    user_id: UUID
    status: str
    generated_at: datetime
    adapted_at: datetime | None = None
    stages: list[PlanStageRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PlanStageStatusUpdate(BaseModel):
    status: Literal["pending", "in_progress", "done"]
