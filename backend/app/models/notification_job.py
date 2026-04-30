import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import BIGINT, UUID

from app.database import Base


class NotificationJob(Base):
    __tablename__ = "notification_jobs"
    __table_args__ = (
        CheckConstraint(
            "type IN ('focus_end', 'break_end')",
            name="ck_notification_jobs_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'sent', 'failed', 'cancelled')",
            name="ck_notification_jobs_status",
        ),
        Index(
            "ix_notification_jobs_pending_scheduled_at",
            "scheduled_at",
            postgresql_where=text("status = 'pending'"),
        ),
        Index("ix_notification_jobs_focus_session", "focus_session_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    focus_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("focus_log.id", ondelete="CASCADE"),
        nullable=False,
    )
    telegram_id = Column(BIGINT, nullable=False)
    type = Column(String(20), nullable=False)
    status = Column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
