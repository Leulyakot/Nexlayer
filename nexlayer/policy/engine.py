"""Policy enforcement engine.

Evaluates incoming prompts against configured policies and returns
a list of enforcement actions (block / redact / flag).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from nexlayer.config.policy_loader import PolicyConfig
from nexlayer.core.schemas import PolicyAction
from nexlayer.detection.detector import DetectionEngine, DetectionResult


@dataclass
class EnforcementResult:
    """Aggregated result of policy evaluation."""

    allowed: bool = True
    modified_prompt: str = ""
    actions: list[PolicyAction] = field(default_factory=list)
    classifications: list[str] = field(default_factory=list)


class PolicyEngine:
    """Runs detection, classification, and enforcement in sequence."""

    def __init__(self, policy: PolicyConfig, detection_engine: DetectionEngine) -> None:
        self._policy = policy
        self._detection = detection_engine

    def evaluate(self, prompt: str, role: str = "viewer") -> EnforcementResult:
        """Evaluate a prompt against all configured policies.

        Returns an EnforcementResult describing whether the request is allowed,
        any modifications applied, and the list of triggered policy actions.
        """
        result = EnforcementResult(modified_prompt=prompt)

        # 1. Content classification (prompt injection, harmful content)
        self._classify(prompt, result)

        # If classification blocked, short-circuit
        if not result.allowed:
            return result

        # 2. Sensitive data detection (PII / CUI)
        detections = self._detection.scan(prompt)
        self._enforce_detections(detections, result)

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _classify(self, prompt: str, result: EnforcementResult) -> None:
        if not self._policy.classification.enabled:
            return

        upper = prompt.upper()
        for category in self._policy.classification.categories:
            for keyword in category.keywords:
                if keyword.upper() in upper:
                    result.classifications.append(category.name)
                    result.actions.append(
                        PolicyAction(
                            policy_name=f"classification:{category.name}",
                            action=category.action,
                            detail=f"Matched keyword: {keyword}",
                        )
                    )
                    if category.action == "block":
                        result.allowed = False
                    break  # one match per category is sufficient

    def _enforce_detections(
        self, detections: list[DetectionResult], result: EnforcementResult
    ) -> None:
        if not detections:
            return

        # Sort detections by position (descending) so we can replace in-place
        # without shifting indices.
        sorted_detections = sorted(detections, key=lambda d: d.start, reverse=True)

        for det in sorted_detections:
            result.actions.append(
                PolicyAction(
                    policy_name=f"detection:{det.detector}:{det.category}",
                    action=det.action,
                    detail=f"Detected {det.category}",
                )
            )

            if det.action == "block":
                result.allowed = False
            elif det.action == "redact":
                # Replace matched text with redaction placeholder
                prompt = result.modified_prompt
                result.modified_prompt = (
                    prompt[: det.start] + f"[REDACTED:{det.category.upper()}]" + prompt[det.end:]
                )
