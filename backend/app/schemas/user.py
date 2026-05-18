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
    timezone: str = "UTC"
    notifications_enabled: bool = True
    weekly_digest_enabled: bool = True


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    telegram_id: Optional[int] = None
    username: Optional[str] = None
    goal: Optional[str] = None
    deadline: Optional[date] = None
    level: Optional[str] = None
    weekly_hours: Optional[int] = None
    timezone: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    weekly_digest_enabled: Optional[bool] = None


class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
