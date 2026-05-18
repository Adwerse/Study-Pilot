from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from app.schemas.analytics import AnalyticsDataQuality, AnalyticsMetrics


WeeklyDigestDeliveryStatus = Literal["pending", "sent", "failed", "skipped"]
WeeklyDigestResultStatus = Literal["sent", "failed", "skipped"]


@dataclass(frozen=True)
class DigestPeriod:
    week_start: datetime
    week_end: datetime
    week_start_date: date
    timezone: str


@dataclass(frozen=True)
class WeeklyDigestReport:
    period: DigestPeriod
    metrics: AnalyticsMetrics
    data_quality: AnalyticsDataQuality
    summary: str
    recommendations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class WeeklyDigestProcessResult:
    processed: int = 0
    sent: int = 0
    failed: int = 0
    skipped: int = 0


@dataclass(frozen=True)
class WeeklyDigestDeliveryResult:
    user_id: UUID
    status: WeeklyDigestResultStatus
    error_message: str | None = None
