import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class WeeklyReview(Base):
    __tablename__ = "weekly_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(Text, nullable=False, default="UTC")
    status = Column(String(20), nullable=False, default="draft")
    summary = Column(Text, nullable=False)
    insights = Column(JSONB, nullable=False, default=list)
    risks = Column(JSONB, nullable=False, default=list)
    recommendations = Column(JSONB, nullable=False, default=list)
    metrics = Column(JSONB, nullable=False, default=dict)
    proposed_changes = Column(JSONB, nullable=False, default=list)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
