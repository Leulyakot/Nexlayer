"""Role-based access control helpers."""

from __future__ import annotations

from nexlayer.config.policy_loader import PolicyConfig


# Ordered from least to most privileged
ROLE_HIERARCHY: dict[str, int] = {
    "viewer": 0,
    "analyst": 1,
    "admin": 2,
}


def has_model_access(role: str, model: str, policy: PolicyConfig) -> bool:
    """Check whether the given role is allowed to use the specified model."""
    role_perms = policy.model_access.role_permissions.get(role)
    if role_perms is None:
        # Unknown role gets no access
        return False
    return model in role_perms.models


def get_max_tokens(role: str, policy: PolicyConfig) -> int:
    """Return the maximum token budget for the role."""
    role_perms = policy.model_access.role_permissions.get(role)
    if role_perms is None:
        return 0
    return role_perms.max_tokens


def get_rate_limit(role: str, policy: PolicyConfig) -> int:
    """Return the per-minute rate limit for the role."""
    role_perms = policy.model_access.role_permissions.get(role)
    if role_perms is None:
        return 0
    return role_perms.rate_limit
