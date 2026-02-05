"""Load and parse YAML policy configuration."""

from __future__ import annotations

import pathlib
from typing import Any

import yaml
from pydantic import BaseModel


class PatternRule(BaseModel):
    name: str
    pattern: str
    action: str = "redact"


class PIIDetectionConfig(BaseModel):
    enabled: bool = True
    action: str = "redact"
    patterns: list[PatternRule] = []


class CUIDetectionConfig(BaseModel):
    enabled: bool = True
    action: str = "block"
    keywords: list[str] = []


class DataProtectionConfig(BaseModel):
    enabled: bool = True
    pii_detection: PIIDetectionConfig = PIIDetectionConfig()
    cui_detection: CUIDetectionConfig = CUIDetectionConfig()


class RolePermission(BaseModel):
    models: list[str] = []
    max_tokens: int = 4096
    rate_limit: int = 60


class ModelAccessConfig(BaseModel):
    default_models: list[str] = []
    restricted_models: list[str] = []
    role_permissions: dict[str, RolePermission] = {}


class ClassificationCategory(BaseModel):
    name: str
    keywords: list[str] = []
    action: str = "flag"


class ClassificationConfig(BaseModel):
    enabled: bool = True
    categories: list[ClassificationCategory] = []


class ComplianceConfig(BaseModel):
    require_audit_log: bool = True
    log_prompt_hash: bool = True
    log_response_metadata: bool = True
    data_retention_days: int = 90


class PolicyConfig(BaseModel):
    data_protection: DataProtectionConfig = DataProtectionConfig()
    model_access: ModelAccessConfig = ModelAccessConfig()
    classification: ClassificationConfig = ClassificationConfig()
    compliance: ComplianceConfig = ComplianceConfig()


def load_policies(path: str) -> PolicyConfig:
    """Load policies from a YAML file path."""
    policy_path = pathlib.Path(path)
    if not policy_path.exists():
        return PolicyConfig()

    with open(policy_path) as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    policies_data = raw.get("policies", {})
    return PolicyConfig(**policies_data)
