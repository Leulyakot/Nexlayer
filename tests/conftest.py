"""Shared test fixtures."""

from __future__ import annotations

import os

# Force test environment before any imports
os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["API_KEYS"] = "test-key-1,test-key-2"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"

import pytest
from httpx import ASGITransport, AsyncClient

from nexlayer.config.policy_loader import load_policies, PolicyConfig
from nexlayer.auth.jwt_handler import create_access_token


@pytest.fixture
def policy() -> PolicyConfig:
    return load_policies("config/policies.yaml")


@pytest.fixture
def admin_token() -> str:
    return create_access_token({"sub": "test-admin", "role": "admin"})


@pytest.fixture
def analyst_token() -> str:
    return create_access_token({"sub": "test-analyst", "role": "analyst"})


@pytest.fixture
def viewer_token() -> str:
    return create_access_token({"sub": "test-viewer", "role": "viewer"})
