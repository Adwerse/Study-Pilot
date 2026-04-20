from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FocusSession(BaseModel):
    id: str
    user_id: str
    stage_id: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    duration_minutes: int | None = None
    topic: str
    difficulty: int | None = Field(default=None, ge=1, le=5)
    completed: bool = False

    model_config = ConfigDict(from_attributes=True)
