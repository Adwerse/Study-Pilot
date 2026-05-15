from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


WeeklyReviewStatus = Literal["draft", "applied", "dismissed"]
RoadmapStatus = Literal["on_track", "behind", "ahead", "insufficient_data"]
ProposedChangeType = Literal[
    "reschedule_stage",
    "split_stage",
    "adjust_stage_focus",
    "mark_stage_at_risk",
]


class WeeklyReviewGenerateRequest(BaseModel):
    plan_id: UUID | None = None
    week_start: date | None = None
    timezone: str | None = None
    apply_changes: bool = False


class WeeklyReviewPeriod(BaseModel):
    start: datetime
    end: datetime
    timezone: str


class WeeklyReviewMetrics(BaseModel):
    planned_focus_minutes: int | None = None
    actual_focus_minutes: int = 0
    completion_rate: int | None = None
    completed_stages_count: int = 0
    planned_stages_count: int = 0
    total_stages_count: int = 0
    roadmap_progress_percent: int = 0


class ProposedChange(BaseModel):
    type: ProposedChangeType
    stage_id: UUID | None = None
    reason: str
    old_start_date: date | None = None
    old_end_date: date | None = None
    new_start_date: date | None = None
    new_end_date: date | None = None
    suggested_new_titles: list[str] | None = None
    note: str | None = None
    suggested_focus_minutes_per_day: int | None = None
    risk_level: Literal["low", "medium", "high"] | None = None


class WeeklyReviewResponse(BaseModel):
    review_id: UUID
    plan_id: UUID
    period: WeeklyReviewPeriod
    status: WeeklyReviewStatus
    roadmap_status: RoadmapStatus
    summary: str
    insights: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    metrics: WeeklyReviewMetrics
    proposed_changes: list[ProposedChange] = Field(default_factory=list)


class ApplyWeeklyReviewResponse(BaseModel):
    review_id: UUID
    status: Literal["applied"]
    applied_changes_count: int
    skipped_changes: list[ProposedChange] | None = None


class WeeklyReviewHistoryItem(BaseModel):
    review_id: UUID
    plan_id: UUID
    period_start: datetime
    period_end: datetime
    status: WeeklyReviewStatus
    roadmap_status: RoadmapStatus
    summary: str
    created_at: datetime


class WeeklyReviewHistoryResponse(BaseModel):
    items: list[WeeklyReviewHistoryItem]
    total: int
    limit: int
    offset: int
