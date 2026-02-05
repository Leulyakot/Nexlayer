"""Tests for the sensitive data detection engine."""

from nexlayer.config.policy_loader import load_policies
from nexlayer.detection.detector import (
    RegexPIIDetector,
    KeywordCUIDetector,
    MLDetector,
    build_detection_engine,
)


def test_email_detection(policy):
    detector = RegexPIIDetector(policy)
    results = detector.detect("Contact me at john@example.com please")
    assert len(results) == 1
    assert results[0].category == "email"
    assert results[0].matched_text == "john@example.com"
    assert results[0].action == "redact"


def test_ssn_detection(policy):
    detector = RegexPIIDetector(policy)
    results = detector.detect("My SSN is 123-45-6789")
    assert len(results) == 1
    assert results[0].category == "ssn"
    assert results[0].action == "block"


def test_phone_detection(policy):
    detector = RegexPIIDetector(policy)
    results = detector.detect("Call me at (555) 123-4567")
    assert len(results) == 1
    assert results[0].category == "phone_us"


def test_credit_card_detection(policy):
    detector = RegexPIIDetector(policy)
    results = detector.detect("Card: 4111-1111-1111-1111")
    assert len(results) == 1
    assert results[0].category == "credit_card"
    assert results[0].action == "block"


def test_no_false_positive_on_clean_text(policy):
    detector = RegexPIIDetector(policy)
    results = detector.detect("Hello, this is a normal prompt about weather.")
    assert len(results) == 0


def test_cui_keyword_detection(policy):
    detector = KeywordCUIDetector(policy)
    results = detector.detect("This document is CONTROLLED and FOR OFFICIAL USE ONLY")
    assert len(results) == 2
    categories = {r.matched_text.upper() for r in results}
    assert "CONTROLLED" in categories
    assert "FOR OFFICIAL USE ONLY" in categories


def test_cui_case_insensitive(policy):
    detector = KeywordCUIDetector(policy)
    results = detector.detect("this is fouo material")
    assert len(results) == 1
    assert results[0].action == "block"


def test_ml_detector_stub(policy):
    detector = MLDetector()
    results = detector.detect("Any text here")
    assert results == []


def test_detection_engine_aggregates(policy):
    engine = build_detection_engine(policy)
    results = engine.scan("Email john@example.com, document is CUI classified")
    # Should have at least email PII and CUI keyword
    categories = {r.category for r in results}
    assert "email" in categories
    assert "cui" in categories


def test_multiple_pii_in_single_text(policy):
    detector = RegexPIIDetector(policy)
    text = "Contact john@example.com or jane@test.org, SSN 123-45-6789"
    results = detector.detect(text)
    assert len(results) == 3  # 2 emails + 1 SSN
