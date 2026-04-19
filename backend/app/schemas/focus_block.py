from pydantic import BaseModel, ConfigDict, Field


class FocusBlock(BaseModel):
    title: str
    topic: str
    duration_minutes: int = Field(ge=15, le=90)
    description: str
    priority: int = Field(ge=1, le=4)


class DailyPlan(BaseModel):
    blocks: list[FocusBlock] = Field(min_length=2, max_length=4)
    daily_note: str

    model_config = ConfigDict(from_attributes=True)
