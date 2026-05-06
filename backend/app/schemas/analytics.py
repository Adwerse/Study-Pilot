from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class AnalyticsPeriodType(str, Enum):
    daily = "daily"
    weekly = "weekly"


class AnalyticsDataQuality(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class AnalyticsPeriod(BaseModel):
    type: AnalyticsPeriodType
    start: datetime
    end: datetime
    timezone: str


class TopicFocusMetric(BaseModel):
    topic: str
    minutes: int


class PlanProgressMetric(BaseModel):
    plan_id: UUID
    title: str
    total_stages: int
    completed_stages: int
    progress_percent: int
    current_stage_id: UUID | None = None
    current_stage_title: str | None = None


class AnalyticsMetrics(BaseModel):
    total_focus_seconds: int = 0
    total_focus_minutes: int = 0
    sessions_count: int = 0
    cancelled_sessions_count: int = 0
    completion_rate: int = 0
    average_session_minutes: int | None = None
    streak_days: int = 0
    best_focus_hours: list[str] = Field(default_factory=list)
    most_focused_topics: list[TopicFocusMetric] = Field(default_factory=list)
    plan_progress: PlanProgressMetric | None = None


class DailyBreakdownItem(BaseModel):
    date: date
    focus_minutes: int = 0
    sessions_count: int = 0
    completion_rate: int = 0


class AnalyticsNarrative(BaseModel):
    summary: str
    recommendations: list[str] = Field(default_factory=list)


class AnalyticsReportResponse(BaseModel):
    period: AnalyticsPeriod
    metrics: AnalyticsMetrics
    summary: str
    recommendations: list[str] = Field(default_factory=list)
    data_quality: AnalyticsDataQuality
    daily_breakdown: list[DailyBreakdownItem] | None = None
