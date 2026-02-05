"""Structured audit logging engine.

All AI interactions are logged as structured JSON records, both to
the application log stream and to the database for queryability.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from nexlayer.core.schemas import PolicyAction

logger = structlog.get_logger("nexlayer.audit")


def _hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()


class AuditEntry:
    """Represents a single audit record."""

    def __init__(
        self,
        *,
        request_id: uuid.UUID,
        user_id: str,
        model_provider: str,
        prompt: str,
        policy_actions: list[PolicyAction],
        classification_results: list[str],
        response_status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.request_id = request_id
        self.user_id = user_id
        self.model_provider = model_provider
        self.timestamp = datetime.now(timezone.utc)
        self.policy_actions = policy_actions
        self.prompt_hash = _hash_prompt(prompt)
        self.classification_results = classification_results
        self.response_status = response_status
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": str(self.request_id),
            "user_id": self.user_id,
            "model_provider": self.model_provider,
            "timestamp": self.timestamp.isoformat(),
            "policy_actions": [a.model_dump() for a in self.policy_actions],
            "prompt_hash": self.prompt_hash,
            "classification_results": self.classification_results,
            "response_status": self.response_status,
            "metadata": self.metadata,
        }


class AuditLogger:
    """Writes audit entries to structured log output and optionally to DB."""

    async def log(self, entry: AuditEntry) -> None:
        """Emit the audit entry as structured JSON log."""
        logger.info(
            "audit_record",
            **entry.to_dict(),
        )

    async def log_to_db(self, entry: AuditEntry, db_session: Any) -> None:
        """Persist audit entry to the database."""
        from nexlayer.database.models import AuditLog

        record = AuditLog(
            request_id=entry.request_id,
            user_id=entry.user_id,
            model_provider=entry.model_provider,
            timestamp=entry.timestamp,
            policy_actions=[a.model_dump() for a in entry.policy_actions],
            prompt_hash=entry.prompt_hash,
            classification_results=entry.classification_results,
            response_status=entry.response_status,
            metadata=entry.metadata,
        )
        db_session.add(record)
        await db_session.flush()
