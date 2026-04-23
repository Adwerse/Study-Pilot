import uuid

from sqlalchemy import Column, Date, DateTime, Integer, Text, func
from sqlalchemy.dialects.postgresql import BIGINT, UUID

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BIGINT, unique=True, nullable=False)
    username = Column(Text, nullable=True)
    goal = Column(Text, nullable=True)
    deadline = Column(Date, nullable=True)
    level = Column(Text, nullable=True)
    weekly_hours = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
