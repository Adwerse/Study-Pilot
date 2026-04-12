from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlanBase(BaseModel):
    user_id: UUID
    title: str
    status: str = "active"


class PlanCreate(PlanBase):
    pass


class PlanUpdate(PlanBase):
    user_id: Optional[UUID] = None
    title: Optional[str] = None
    status: Optional[str] = None


class PlanRead(PlanBase):
    id: UUID
    generated_at: datetime
    adapted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)