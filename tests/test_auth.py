"""Tests for authentication and RBAC."""

from jose import jwt

from nexlayer.auth.jwt_handler import create_access_token, decode_access_token
from nexlayer.auth.rbac import has_model_access, get_max_tokens, get_rate_limit
from nexlayer.config.policy_loader import load_policies


def test_create_and_decode_jwt():
    token = create_access_token({"sub": "user1", "role": "admin"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user1"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_jwt_contains_expiry():
    token = create_access_token({"sub": "user2"})
    payload = decode_access_token(token)
    assert "exp" in payload


def test_admin_has_all_model_access(policy):
    assert has_model_access("admin", "openai", policy) is True
    assert has_model_access("admin", "anthropic", policy) is True
    assert has_model_access("admin", "local", policy) is True


def test_analyst_has_limited_access(policy):
    assert has_model_access("analyst", "openai", policy) is True
    assert has_model_access("analyst", "anthropic", policy) is True
    assert has_model_access("analyst", "local", policy) is False


def test_viewer_has_minimal_access(policy):
    assert has_model_access("viewer", "openai", policy) is True
    assert has_model_access("viewer", "anthropic", policy) is False
    assert has_model_access("viewer", "local", policy) is False


def test_unknown_role_denied(policy):
    assert has_model_access("unknown", "openai", policy) is False


def test_max_tokens_by_role(policy):
    assert get_max_tokens("admin", policy) == 8192
    assert get_max_tokens("analyst", policy) == 4096
    assert get_max_tokens("viewer", policy) == 2048


def test_rate_limit_by_role(policy):
    assert get_rate_limit("admin", policy) == 120
    assert get_rate_limit("analyst", policy) == 60
    assert get_rate_limit("viewer", policy) == 30
