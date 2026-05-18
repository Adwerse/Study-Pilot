import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import BIGINT, UUID

from app.database import Base


class WeeklyDigestDelivery(Base):
    __tablename__ = "weekly_digest_deliveries"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'sent', 'failed', 'skipped')",
            name="ck_weekly_digest_deliveries_status",
        ),
        UniqueConstraint(
            "user_id",
            "week_start",
            "week_end",
            name="ux_weekly_digest_deliveries_user_week",
        ),
        Index("ix_weekly_digest_deliveries_user_created", "user_id", "created_at"),
        Index("ix_weekly_digest_deliveries_status_created", "status", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    telegram_id = Column(BIGINT, nullable=False)
    week_start = Column(DateTime(timezone=True), nullable=False)
    week_end = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(Text, nullable=False, default="UTC", server_default="UTC")
    status = Column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    message_text = Column(Text, nullable=True)
    telegram_message_id = Column(BIGINT, nullable=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
