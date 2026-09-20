"""
ELEOS — Member 1 Phase 2: Real-World Document Ingestion & Verification Test Suite

Tests:
1. Document Hashing & SHA-256 Digest Anchoring.
2. Canonical Schema instantiation, validation, and serialization.
3. Multimodal Extraction via Gemini and AWS Native Pipeline simulation.
4. Schema Parity between extraction providers.
5. Zero-Trust Verification Engine:
   - Accounting identity checks (itemized expenses vs. total expenditure).
   - ICAI UDIN 18-character audit verification.
   - Statutory registry cross-checks (Darpan, 12A/80G, FCRA).
   - Project-to-financial grant cross-reconciliation (detecting phantom projects).
6. Canonical-to-Features Adapter & Isolation Forest ML scoring.
7. End-to-End Document Pipeline output conformity to Section 47 explainable JSON schema.
"""

import sys
import json
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.schemas.canonical_document_schema import (
    CanonicalNgoDocumentBundle,
    CanonicalIdentity,
    CanonicalTaxCompliance,
    CanonicalAnnualFinancial,
    CanonicalProject,
    ExtractedField,
)
from scripts.extract.gemini_extractor import (
    compute_file_sha256,
    extract_ngo_document_package_gemini,
)
from scripts.extract.aws_extractor import extract_ngo_document_package_aws
from scripts.extract.document_verifier import run_zero_trust_verification
from scripts.extract.canonical_to_features import canonical_bundle_to_member1_inputs
from scripts.run_document_pipeline import process_document_package
from scripts.sample_generator.generate_sample_pdfs import generate_all_sample_pdfs


SAMPLE_DOCS_DIR = ROOT_DIR / "data" / "sample_docs"
CLEAN_PDF = SAMPLE_DOCS_DIR / "NGO_Clean.pdf"
HIGH_ADMIN_PDF = SAMPLE_DOCS_DIR / "NGO_HighAdmin.pdf"
FRAUD_PDF = SAMPLE_DOCS_DIR / "NGO_Anomaly_Case.pdf"


@pytest.fixture(scope="session", autouse=True)
def ensure_sample_pdfs():
    """Ensures sample test PDFs exist before running tests."""
    if not (CLEAN_PDF.exists() and HIGH_ADMIN_PDF.exists() and FRAUD_PDF.exists()):
        generate_all_sample_pdfs()
    assert CLEAN_PDF.exists()
    assert HIGH_ADMIN_PDF.exists()
    assert FRAUD_PDF.exists()


# --------------------------------------------------------------------------
# 1. Document Hashing & Integrity Tests
# --------------------------------------------------------------------------
def test_document_hashing():
    """Verify SHA-256 calculation produces 0x-prefixed 64-char hex string and is deterministic."""
    hash_1 = compute_file_sha256(CLEAN_PDF)
    hash_2 = compute_file_sha256(CLEAN_PDF)

    assert isinstance(hash_1, str)
    assert hash_1.startswith("0x")
    assert len(hash_1) == 66  # "0x" + 64 hex chars
    assert hash_1 == hash_2
    assert all(c in "0123456789abcdef" for c in hash_1[2:])

    fraud_hash = compute_file_sha256(FRAUD_PDF)
    assert hash_1 != fraud_hash


# --------------------------------------------------------------------------
# 2. Canonical Schema Validation Tests
# --------------------------------------------------------------------------
def test_canonical_schema_instantiation():
    """Verify Pydantic models enforce types and extract confidence/provenance."""
    bundle = CanonicalNgoDocumentBundle(
        extraction_provider="standard_reference",
        raw_document_hashes={"test.pdf": "0x" + "a" * 64},
        identity=CanonicalIdentity(
            ngo_name=ExtractedField(value="Aarogya Seva Trust", confidence=0.99, page_number=1),
            registration_type=ExtractedField(value="Trust", confidence=0.95),
            registration_number=ExtractedField(value="TR/2016/DEL/00891"),
            registration_authority=ExtractedField(value="Sub-Registrar Delhi"),
            act_name=ExtractedField(value="Indian Trusts Act, 1882"),
            date_of_registration=ExtractedField(value="2016-03-15"),
            pan=ExtractedField(value="AAATA9921D"),
            state=ExtractedField(value="Delhi"),
            district=ExtractedField(value="Central Delhi"),
        ),
        compliance=CanonicalTaxCompliance(
            has_12a=ExtractedField(value=True),
            has_80g=ExtractedField(value=True),
            fcra_status=ExtractedField(value="Valid"),
        ),
        financials=[
            CanonicalAnnualFinancial(
                financial_year=ExtractedField(value="2023-24"),
                audit_opinion=ExtractedField(value="Clean"),
                total_income=ExtractedField(value=10000000.0),
                total_expenditure=ExtractedField(value=9500000.0),
                programme_expenses=ExtractedField(value=8000000.0),
                administrative_expenses=ExtractedField(value=1500000.0),
                fundraising_expenses=ExtractedField(value=0.0),
                udin=ExtractedField(value="24056789ABCDEF1234"),
            )
        ],
        projects=[
            CanonicalProject(
                project_name=ExtractedField(value="Rural Health Outreach"),
                status=ExtractedField(value="Completed"),
                reported_cost=ExtractedField(value=6000000.0),
            )
        ],
    )

    assert bundle.identity.ngo_name.value == "Aarogya Seva Trust"
    assert bundle.identity.ngo_name.confidence == 0.99
    assert bundle.financials[0].total_income.value == 10000000.0
    assert bundle.financials[0].udin.value == "24056789ABCDEF1234"

    # Verify JSON serialization round-trip
    serialized = bundle.model_dump_json()
    deserialized = CanonicalNgoDocumentBundle.model_validate_json(serialized)
    assert deserialized.identity.pan.value == "AAATA9921D"


# --------------------------------------------------------------------------
# 3. Multimodal Extraction & Provider Parity Tests
# --------------------------------------------------------------------------
def test_gemini_extraction_clean():
    """Verify Gemini multimodal extractor extracts valid bundle from clean PDF."""
    bundle = extract_ngo_document_package_gemini(CLEAN_PDF)
    assert isinstance(bundle, CanonicalNgoDocumentBundle)
    assert bundle.extraction_provider == "gemini"
    assert bundle.identity.ngo_name.value == "HopeRelief Foundation"
    assert bundle.identity.pan.value == "AAATH1234F"
    assert len(bundle.financials) >= 1
    assert bundle.financials[0].financial_year.value == "FY2024-25"
    assert bundle.financials[0].total_income.value == 23200000.0


def test_aws_extraction_clean():
    """Verify AWS Textract/Bedrock extractor extracts valid bundle from clean PDF."""
    bundle = extract_ngo_document_package_aws(CLEAN_PDF)
    assert isinstance(bundle, CanonicalNgoDocumentBundle)
    assert bundle.extraction_provider == "aws_textract_bedrock"
    assert bundle.identity.ngo_name.value == "HopeRelief Foundation"
    assert bundle.identity.pan.value == "AAATH1234F"
    assert len(bundle.financials) >= 1
    assert bundle.financials[0].financial_year.value == "FY2024-25"
    assert bundle.financials[0].total_income.value == 23200000.0


def test_extraction_provider_parity():
    """Verify both Gemini and AWS providers yield identical core financial values."""
    bundle_gemini = extract_ngo_document_package_gemini(CLEAN_PDF)
    bundle_aws = extract_ngo_document_package_aws(CLEAN_PDF)

    assert bundle_gemini.identity.pan.value == bundle_aws.identity.pan.value
    assert bundle_gemini.identity.registration_type.value == bundle_aws.identity.registration_type.value
    assert bundle_gemini.financials[0].total_income.value == bundle_aws.financials[0].total_income.value
    assert bundle_gemini.financials[0].total_expenditure.value == bundle_aws.financials[0].total_expenditure.value
    assert bundle_gemini.financials[0].programme_expenses.value == bundle_aws.financials[0].programme_expenses.value
    assert bundle_gemini.financials[0].administrative_expenses.value == bundle_aws.financials[0].administrative_expenses.value


# --------------------------------------------------------------------------
# 4. Zero-Trust Verification Engine Tests
# --------------------------------------------------------------------------
def test_zero_trust_clean_ngo():
    """Clean NGO should pass core checks."""
    bundle = extract_ngo_document_package_gemini(CLEAN_PDF)
    verif = run_zero_trust_verification(bundle)

    assert verif["overall_verification_status"] == "PASSED"
    checks = verif["verification_checks"]
    assert checks["accounting_reconciliation"]["pass"] is True
    assert checks["icai_udin_verified"] is True
    assert checks["project_grant_cross_reconciliation"] is True
    assert checks["pan_format_valid"] is True
    assert checks["external_registries"]["darpan_verified"] is True


def test_zero_trust_fraudulent_ngo():
    """Fraudulent NGO must trigger accounting mismatch, missing UDIN, and uncorroborated project claim."""
    bundle = extract_ngo_document_package_gemini(FRAUD_PDF)
    verif = run_zero_trust_verification(bundle)

    assert verif["overall_verification_status"] == "SCRUTINY_REQUIRED"
    assert len(verif["critical_flags"]) >= 2

    # 1. Accounting identity failure: expenditure declared != sum of items (INR 15L difference)
    acc_check = verif["verification_checks"]["accounting_reconciliation"]
    assert acc_check["pass"] is False
    assert acc_check["variance_inr"] == 1500000.0

    # 2. UDIN missing failure
    assert verif["verification_checks"]["icai_udin_verified"] is False

    # 3. Project grant cross-reconciliation discrepancy
    assert verif["verification_checks"]["project_grant_cross_reconciliation"] is False

    # Verify flags contain explicit forensic details
    flags_str = " ".join(verif["critical_flags"])
    assert "Material Accounting Discrepancy" in flags_str
    assert "UDIN" in flags_str
    assert "Uncorroborated Project Claim" in flags_str


def test_zero_trust_high_admin_ngo():
    """High-admin NGO should detect expired 80G tax certification."""
    bundle = extract_ngo_document_package_gemini(HIGH_ADMIN_PDF)
    verif = run_zero_trust_verification(bundle)

    # High Admin NGO has expired 80G certification
    tax_check = verif["verification_checks"]["tax_exemptions"]
    assert tax_check["section_80g_active"] is False

    flags_str = " ".join(verif["critical_flags"])
    assert "80G" in flags_str or "expired" in flags_str.lower()


# --------------------------------------------------------------------------
# 5. Canonical to Feature Adapter & Isolation Forest Tests
# --------------------------------------------------------------------------
def test_canonical_to_features_adaptation():
    """Verify feature adapter generates complete feature rows conforming to Member 1 pipeline."""
    bundle = extract_ngo_document_package_gemini(CLEAN_PDF)
    verif = run_zero_trust_verification(bundle)
    m_row, p_row, f_row, o_row, df_fin_reports = canonical_bundle_to_member1_inputs(bundle, verif)

    # Master row checks
    assert m_row["ngo_id"] == "LIVE_AAATH1234F"
    assert m_row["registration_type"] == "Trust"
    assert m_row["pan_verified"] is True

    # Financial features checks
    assert f_row["programme_expense_ratio"] == pytest.approx(0.819, abs=0.01)
    assert f_row["administrative_expense_ratio"] == pytest.approx(0.090, abs=0.01)
    assert "financial_anomaly_score" in f_row
    assert "financial_anomaly_label" in f_row

    # Financial anomaly detection: Clean NGO should be Normal
    assert f_row["financial_anomaly_label"] == "Normal"
    assert f_row["financial_anomaly_score"] > 0.0


def test_isolation_forest_outlier_detection():
    """Verify that High-Admin NGO (48% admin) triggers outlier label in Isolation Forest."""
    bundle = extract_ngo_document_package_gemini(HIGH_ADMIN_PDF)
    verif = run_zero_trust_verification(bundle)
    _, _, f_row, _, _ = canonical_bundle_to_member1_inputs(bundle, verif)

    # High Admin ratio (48%) is far outside normal distribution (~10-15%)
    assert f_row["administrative_expense_ratio"] > 0.45
    assert f_row["financial_anomaly_label"] == "Outlier"
    assert f_row["financial_anomaly_score"] < 0.0


# --------------------------------------------------------------------------
# 6. End-to-End Document Pipeline Integration Tests
# --------------------------------------------------------------------------
def test_end_to_end_clean_ngo_pipeline():
    """Verify complete end-to-end execution on Clean NGO produces valid Section 47 JSON assessment."""
    assessment = process_document_package(CLEAN_PDF, provider="gemini")

    assert "ngo_id" in assessment
    assert assessment["ngo_id"] == "LIVE_AAATH1234F"
    assert "trustability_score" in assessment
    score = assessment["trustability_score"]
    assert 0.0 <= score <= 100.0
    # Clean NGO should score high (>= 75.0)
    assert score >= 75.0

    # Verify 4 dimensions
    dims = assessment["dimension_scores"]
    assert "identity_legal" in dims
    assert "financial_transparency" in dims
    assert "operational_evidence" in dims
    assert "data_completeness" in dims

    # Verify real-world Phase 2 extensions attached
    assert "raw_document_hashes" in assessment
    assert len(assessment["raw_document_hashes"]) > 0
    assert "verification_summary" in assessment
    assert assessment["verification_summary"]["status"] == "PASSED"


def test_end_to_end_fraudulent_ngo_pipeline():
    """Verify complete end-to-end execution on Fraudulent NGO produces penalized score and flags."""
    assessment = process_document_package(FRAUD_PDF, provider="gemini")

    assert assessment["ngo_id"] == "LIVE_AAATP9876K"
    assert "verification_summary" in assessment
    assert assessment["verification_summary"]["status"] == "SCRUTINY_REQUIRED"

    # Score should be significantly penalized due to missing UDIN and balance sheet mismatch
    score = assessment["trustability_score"]
    assert score < 65.0

    # Must contain negative evidence or verification checks
    assert len(assessment["verification_summary"]["checks"]) > 0


def test_end_to_end_aws_provider():
    """Verify complete end-to-end execution via AWS provider produces equivalent valid assessment."""
    assessment = process_document_package(CLEAN_PDF, provider="aws")

    assert assessment["extraction_provider"] == "aws_textract_bedrock"
    assert assessment["verification_summary"]["status"] == "PASSED"
    assert assessment["trustability_score"] >= 75.0


# --------------------------------------------------------------------------
# 7. Edge Cases & Failure Handling Tests
# --------------------------------------------------------------------------
def test_missing_file_raises_filenotfound(tmp_path):
    """Verify that a nonexistent document path raises FileNotFoundError."""
    nonexistent = tmp_path / "nonexistent.pdf"
    with pytest.raises(FileNotFoundError):
        process_document_package(nonexistent, provider="gemini")
    with pytest.raises(FileNotFoundError):
        process_document_package(nonexistent, provider="aws")


def test_empty_file_raises_valueerror(tmp_path):
    """Verify that an empty (0-byte) PDF raises ValueError."""
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        process_document_package(empty_pdf, provider="gemini")
    with pytest.raises(ValueError, match="empty"):
        process_document_package(empty_pdf, provider="aws")


def test_corrupted_pdf_graceful_handling(tmp_path):
    """Verify that a corrupted PDF is handled gracefully without crashing, yielding low confidence and scrutiny status."""
    corrupt_pdf = tmp_path / "corrupt.pdf"
    corrupt_pdf.write_bytes(b"%PDF-1.4 RANDOM_CORRUPT_BYTES_NOT_PARSABLE")

    assessment = process_document_package(corrupt_pdf, provider="gemini")
    assert assessment["verification_summary"]["status"] == "SCRUTINY_REQUIRED"
    assert assessment["trustability_score"] < 40.0
    assert assessment["confidence_band"] == "Low"
    assert "Unrecognized Document" in assessment["ngo_name"]

    out_file = ROOT_DIR / "outputs" / f"live_assessment_{corrupt_pdf.stem}.json"
    if out_file.exists():
        out_file.unlink()
