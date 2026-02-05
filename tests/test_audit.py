"""Tests for the audit logging engine."""

import uuid

import pytest

from nexlayer.audit.logger import AuditEntry, AuditLogger, _hash_prompt
from nexlayer.core.schemas import PolicyAction


def test_hash_prompt_deterministic():
    h1 = _hash_prompt("test prompt")
    h2 = _hash_prompt("test prompt")
    assert h1 == h2


def test_hash_prompt_differs():
    h1 = _hash_prompt("prompt A")
    h2 = _hash_prompt("prompt B")
    assert h1 != h2


def test_audit_entry_to_dict():
    entry = AuditEntry(
        request_id=uuid.uuid4(),
        user_id="user-1",
        model_provider="openai",
        prompt="hello",
        policy_actions=[
            PolicyAction(policy_name="test", action="flag", detail="test detail")
        ],
        classification_results=["safe"],
        response_status="success",
    )
    d = entry.to_dict()
    assert d["user_id"] == "user-1"
    assert d["model_provider"] == "openai"
    assert d["response_status"] == "success"
    assert len(d["policy_actions"]) == 1
    assert d["prompt_hash"] == _hash_prompt("hello")


@pytest.mark.asyncio
async def test_audit_logger_emits():
    """Audit logger should not raise on log()."""
    logger = AuditLogger()
    entry = AuditEntry(
        request_id=uuid.uuid4(),
        user_id="user-1",
        model_provider="anthropic",
        prompt="test",
        policy_actions=[],
        classification_results=[],
        response_status="success",
    )
    await logger.log(entry)  # Should not raise
