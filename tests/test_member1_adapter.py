"""
Tests for Member 1 Integration Adapter and Backend Bridge.
Verifies that Member 1's live extraction, zero-trust verification,
canonical schema mapping, and trustability scores properly integrate
with backend API contracts and frontend-expected data formats.
"""

import sys
import uuid
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from backend.services.member1_adapter import (
    load_cached_assessment,
    adapt_assessment_to_backend,
    process_uploaded_document_package,
    SEED_NGO_MAP
)


def test_load_cached_assessment_clean():
    """Verify loading cached assessment for clean NGO."""
    assessment = load_cached_assessment("NGO_Clean")
    assert assessment is not None, "Failed to load NGO_Clean assessment"
    assert "trustability_score" in assessment
    assert "dimension_scores" in assessment
    assert assessment["dimension_scores"]["identity_legal"] > 0


def test_load_cached_assessment_anomaly():
    """Verify loading cached assessment for anomaly NGO."""
    assessment = load_cached_assessment("NGO_Anomaly_Case")
    assert assessment is not None, "Failed to load NGO_Anomaly_Case assessment"
    assert assessment["trustability_score"] < 60.0
    assert "Outlier" in assessment["financial_analysis"]["financial_anomaly_label"]


def test_seed_ngo_map_resolution():
    """Verify that seed database UUIDs correctly map to Member 1 assessments."""
    for seed_uuid, expected_key in SEED_NGO_MAP.items():
        assessment = load_cached_assessment(seed_uuid)
        assert assessment is not None, f"Failed to map seed UUID {seed_uuid} to {expected_key}"
        assert "trustability_score" in assessment


def test_adapt_assessment_dual_key_compatibility():
    """
    Verify that adapt_assessment_to_backend produces all keys expected by
    the legacy backend, /ngos/[id], /ngo/organisation, and /reviewer.
    """
    raw_assessment = load_cached_assessment("NGO_Clean")
    assert raw_assessment is not None

    adapted = adapt_assessment_to_backend(raw_assessment)

    # 1. Scalar scores
    assert "overall_score" in adapted
    assert "trust_score" in adapted
    assert "trustability_score" in adapted
    assert adapted["overall_score"] == adapted["trust_score"]

    # 2. Dual-key breakdown for frontend compatibility
    breakdown = adapted["breakdown"]
    # Keys for /ngo/organisation
    assert "legal" in breakdown
    assert "financial" in breakdown
    assert "operational" in breakdown
    assert "completeness" in breakdown
    # Keys for scoring_service / reviewer
    assert "identity_legal" in breakdown
    assert "financial_transparency" in breakdown
    assert "operational_evidence" in breakdown
    assert "data_completeness" in breakdown

    # Values must match between alias pairs
    assert breakdown["legal"] == breakdown["identity_legal"]
    assert breakdown["financial"] == breakdown["financial_transparency"]
    assert breakdown["operational"] == breakdown["operational_evidence"]
    assert breakdown["completeness"] == breakdown["data_completeness"]

    # 3. Evidence and Telemetry
    assert "positive_evidence" in adapted
    assert "negative_evidence" in adapted
    assert "financial_analysis" in adapted
    assert "score_interpretation" in adapted
    assert "is_member1_verified" in adapted
    assert adapted["is_member1_verified"] is True
    assert "extraction_provider" in adapted


def test_process_uploaded_document_empty():
    """Verify that empty uploads raise ValueError."""
    with pytest.raises(ValueError, match="empty"):
        process_uploaded_document_package(b"", "test.pdf")


def test_process_uploaded_document_real_pdf():
    """
    Verify full end-to-end ingestion and scoring of an actual PDF file
    through Member 1's pipeline via the adapter.
    """
    pdf_path = ROOT_DIR / "data" / "sample_docs" / "NGO_Clean.pdf"
    assert pdf_path.exists(), f"Sample PDF missing at {pdf_path}"

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    adapted = process_uploaded_document_package(
        file_bytes=file_bytes,
        filename="test_upload_clean.pdf",
        provider="gemini"
    )

    assert adapted is not None
    assert adapted["overall_score"] >= 75
    assert adapted["overall_label"] in ["verified", "partially_verified"]
    assert adapted["is_member1_verified"] is True
    assert adapted["dimension_scores"]["identity_legal"] >= 80.0
    assert len(adapted["positive_evidence"]) > 0

