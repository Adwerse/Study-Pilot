import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class FocusLog(Base):
    __tablename__ = "focus_log"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'completed', 'cancelled')", name="ck_focus_log_status"
        ),
        CheckConstraint(
            "difficulty IS NULL OR difficulty BETWEEN 1 AND 5",
            name="ck_focus_log_difficulty",
        ),
        CheckConstraint(
            "planned_duration_minutes IS NULL OR "
            "(planned_duration_minutes > 0 AND planned_duration_minutes <= 180)",
            name="ck_focus_log_planned_duration",
        ),
        CheckConstraint(
            "actual_duration_seconds IS NULL OR actual_duration_seconds >= 0",
            name="ck_focus_log_actual_duration",
        ),
        CheckConstraint(
            "topic IS NULL OR char_length(topic) <= 255",
            name="ck_focus_log_topic_length",
        ),
        Index(
            "ux_focus_log_one_active_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index("ix_focus_log_user_started_at", "user_id", "started_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    plan_id = Column(
        UUID(as_uuid=True), ForeignKey("plans.id", ondelete="SET NULL"), nullable=True
    )
    plan_stage_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan_stages.id", ondelete="SET NULL"),
        nullable=True,
    )
    topic = Column(String(255), nullable=True)
    status = Column(
        String(20), nullable=False, default="active", server_default="active"
    )
    started_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at = Column(DateTime(timezone=True), nullable=True)
    planned_duration_minutes = Column(Integer, nullable=True)
    actual_duration_seconds = Column(Integer, nullable=True)
    difficulty = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    @property
    def stage_id(self):
        return self.plan_stage_id

    @stage_id.setter
    def stage_id(self, value):
        self.plan_stage_id = value

    @property
    def completed(self) -> bool:
        return self.status == "completed"

    @completed.setter
    def completed(self, value: bool) -> None:
        if value:
            self.status = "completed"
        elif self.status == "completed":
            self.status = "active"

    @property
    def duration_minutes(self) -> int | None:
        if self.actual_duration_seconds is not None:
            return max(1, self.actual_duration_seconds // 60)
        return self.planned_duration_minutes

    @duration_minutes.setter
    def duration_minutes(self, value: int | None) -> None:
        if value is None:
            self.actual_duration_seconds = None
            return
        self.actual_duration_seconds = max(0, int(value) * 60)
