"""Tests for configuration and policy loading."""

from nexlayer.config.settings import get_settings
from nexlayer.config.policy_loader import load_policies, PolicyConfig


def test_settings_load():
    settings = get_settings()
    assert settings.app_env == "test"
    assert settings.jwt_secret_key == "test-secret-key-for-testing-only"


def test_valid_api_keys():
    settings = get_settings()
    assert "test-key-1" in settings.valid_api_keys
    assert "test-key-2" in settings.valid_api_keys


def test_load_policies_from_yaml():
    policy = load_policies("config/policies.yaml")
    assert isinstance(policy, PolicyConfig)
    assert policy.data_protection.enabled is True
    assert policy.data_protection.pii_detection.enabled is True
    assert len(policy.data_protection.pii_detection.patterns) > 0


def test_load_policies_missing_file():
    policy = load_policies("nonexistent.yaml")
    assert isinstance(policy, PolicyConfig)
    # Should return defaults
    assert policy.data_protection.enabled is True


def test_classification_policies_loaded():
    policy = load_policies("config/policies.yaml")
    assert policy.classification.enabled is True
    assert len(policy.classification.categories) > 0
    names = {c.name for c in policy.classification.categories}
    assert "prompt_injection" in names


def test_role_permissions_loaded():
    policy = load_policies("config/policies.yaml")
    assert "admin" in policy.model_access.role_permissions
    assert "analyst" in policy.model_access.role_permissions
    assert "viewer" in policy.model_access.role_permissions


def test_compliance_settings():
    policy = load_policies("config/policies.yaml")
    assert policy.compliance.require_audit_log is True
    assert policy.compliance.data_retention_days == 90
