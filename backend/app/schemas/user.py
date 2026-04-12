from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    goal: Optional[str] = None
    deadline: Optional[date] = None
    level: Optional[str] = None
    weekly_hours: Optional[int] = None


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    telegram_id: Optional[int] = None
    username: Optional[str] = None
    goal: Optional[str] = None
    deadline: Optional[date] = None
    level: Optional[str] = None
    weekly_hours: Optional[int] = None


class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)