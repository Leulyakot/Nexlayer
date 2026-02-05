"""Sensitive data detection engine.

Supports:
- Regex-based PII detection
- Keyword / dictionary-based CUI detection
- Extensible ML detection interface (stub)
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from nexlayer.config.policy_loader import PolicyConfig


@dataclass
class DetectionResult:
    """A single detection finding."""

    detector: str
    category: str
    matched_text: str
    action: str  # block | redact | flag
    start: int = 0
    end: int = 0


class BaseDetector(ABC):
    """Interface all detectors must implement."""

    @abstractmethod
    def detect(self, text: str) -> list[DetectionResult]:
        ...


class RegexPIIDetector(BaseDetector):
    """Detects PII using configurable regex patterns."""

    def __init__(self, policy: PolicyConfig) -> None:
        self._patterns: list[tuple[str, re.Pattern[str], str]] = []
        if policy.data_protection.pii_detection.enabled:
            for rule in policy.data_protection.pii_detection.patterns:
                self._patterns.append(
                    (rule.name, re.compile(rule.pattern), rule.action)
                )

    def detect(self, text: str) -> list[DetectionResult]:
        results: list[DetectionResult] = []
        for name, pattern, action in self._patterns:
            for match in pattern.finditer(text):
                results.append(
                    DetectionResult(
                        detector="regex_pii",
                        category=name,
                        matched_text=match.group(),
                        action=action,
                        start=match.start(),
                        end=match.end(),
                    )
                )
        return results


class KeywordCUIDetector(BaseDetector):
    """Detects CUI markers using keyword matching."""

    def __init__(self, policy: PolicyConfig) -> None:
        self._keywords: list[str] = []
        self._action = "block"
        if policy.data_protection.cui_detection.enabled:
            self._keywords = [k.upper() for k in policy.data_protection.cui_detection.keywords]
            self._action = policy.data_protection.cui_detection.action

    def detect(self, text: str) -> list[DetectionResult]:
        results: list[DetectionResult] = []
        upper_text = text.upper()
        for kw in self._keywords:
            idx = 0
            while True:
                idx = upper_text.find(kw, idx)
                if idx == -1:
                    break
                results.append(
                    DetectionResult(
                        detector="keyword_cui",
                        category="cui",
                        matched_text=text[idx : idx + len(kw)],
                        action=self._action,
                        start=idx,
                        end=idx + len(kw),
                    )
                )
                idx += len(kw)
        return results


class MLDetector(BaseDetector):
    """Stub for ML-based sensitive data detection.

    This is an extensibility hook. In a production deployment this would
    call an ML classification model (e.g., a NER model or transformer-based
    classifier) to identify sensitive data that regex cannot catch.
    """

    def detect(self, text: str) -> list[DetectionResult]:
        # Stub — return empty list
        return []


@dataclass
class DetectionEngine:
    """Aggregates multiple detectors and runs them against input text."""

    detectors: list[BaseDetector] = field(default_factory=list)

    def scan(self, text: str) -> list[DetectionResult]:
        results: list[DetectionResult] = []
        for detector in self.detectors:
            results.extend(detector.detect(text))
        return results


def build_detection_engine(policy: PolicyConfig) -> DetectionEngine:
    """Factory that wires up all configured detectors."""
    return DetectionEngine(
        detectors=[
            RegexPIIDetector(policy),
            KeywordCUIDetector(policy),
            MLDetector(),
        ]
    )
