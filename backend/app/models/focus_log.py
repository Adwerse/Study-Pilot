import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class FocusLog(Base):
    __tablename__ = "focus_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stage_id = Column(UUID(as_uuid=True), ForeignKey("plan_stages.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    topic = Column(Text, nullable=False)
    difficulty = Column(Integer, nullable=True)
    completed = Column(Boolean, nullable=False, default=False)
