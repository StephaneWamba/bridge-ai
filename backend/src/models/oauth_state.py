"""OAuth state model for CSRF protection."""

from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.database import Base


class OAuthState(Base):
    """Temporary OAuth state storage for CSRF protection."""

    __tablename__ = "oauth_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state = Column(String, nullable=False, unique=True, index=True)
    provider = Column(String, nullable=False, index=True)  # hubspot, gmail, etc.
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_oauth_state_provider_expires", "provider", "expires_at"),
    )




