"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class AIRequest(BaseModel):
    """Inbound AI request payload."""

    user_id: str
    model: ModelProvider
    prompt: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyAction(BaseModel):
    """A single policy enforcement action that was applied."""

    policy_name: str
    action: str  # block | redact | flag
    detail: str = ""


class AIResponse(BaseModel):
    """Response returned to the caller."""

    request_id: UUID
    model_provider: str
    response_text: str
    policy_actions: list[PolicyAction] = []
    classification_results: list[str] = []
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    error: str
    detail: str = ""
    request_id: UUID | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = ""
