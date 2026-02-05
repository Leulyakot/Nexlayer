"""SQLAlchemy ORM models for Nexlayer."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, String, Text, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class AuditLog(Base):
    """Immutable audit record for every AI interaction."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    user_id = Column(String(256), nullable=False, index=True)
    model_provider = Column(String(64), nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    policy_actions = Column(JSONB, nullable=False, default=list)
    prompt_hash = Column(String(128), nullable=False)
    classification_results = Column(JSONB, nullable=False, default=list)
    response_status = Column(String(32), nullable=False)
    metadata = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_audit_logs_timestamp", "timestamp"),
    )


class User(Base):
    """Registered user/service account."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(256), nullable=False, unique=True, index=True)
    hashed_password = Column(String(512), nullable=False)
    role = Column(
        Enum("admin", "analyst", "viewer", name="user_role"),
        nullable=False,
        default="viewer",
    )
    api_key = Column(String(512), nullable=True, unique=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    disabled = Column(String(5), nullable=False, default="false")
