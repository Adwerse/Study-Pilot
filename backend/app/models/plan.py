import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="active")
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    adapted_at = Column(DateTime(timezone=True), nullable=True)

    stages = relationship(
        "PlanStage",
        back_populates="plan",
        order_by="PlanStage.order_index",
        cascade="all, delete-orphan",
    )


class PlanStage(Base):
    __tablename__ = "plan_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    week_number = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    deliverable = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    order_index = Column(Integer, nullable=False)

    plan = relationship("Plan", back_populates="stages")
