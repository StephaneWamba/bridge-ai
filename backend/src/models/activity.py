"""Activity log model."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.database import Base


class Activity(Base):
    """Activity log for audit trail."""

    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id"), nullable=False, index=True)
    # tool_execution, approval, error, etc.
    action = Column(String, nullable=False, index=True)
    # hubspot, gmail, etc.
    provider = Column(String, nullable=True, index=True)
    tool_name = Column(String, nullable=True)  # read_contact, send_email, etc.
    # success, error, pending, approved, rejected
    status = Column(String, nullable=False)
    extra_data = Column(JSON, nullable=True)  # Additional context
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow,
                        nullable=False, index=True)
