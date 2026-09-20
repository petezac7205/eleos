"""
Document Pipeline Master Orchestrator.
Executes the complete real-world Member 1 workflow:
Document Ingestion -> Dual Provider Extraction (Gemini / AWS) ->
Zero-Trust Verification -> Canonical Feature Adaptation ->
Isolation Forest ML Inference -> Deterministic Trustability Scoring ->
Section 47 Explainable JSON Assessment.
"""

import sys
import os
import json
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.extract.gemini_extractor import extract_ngo_document_package_gemini, compute_file_sha256
from scripts.extract.aws_extractor import extract_ngo_document_package_aws
from scripts.extract.document_verifier import run_zero_trust_verification
from scripts.extract.canonical_to_features import canonical_bundle_to_member1_inputs
from scripts.trustability_scoring import assess_single_ngo, DEFAULT_WEIGHTS

OUTPUTS_DIR = ROOT_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def process_document_package(pdf_path: Path, provider: str = "gemini") -> dict:
    if not pdf_path.exists():
        raise FileNotFoundError(f"Target document package not found at: {pdf_path}")
    if pdf_path.stat().st_size == 0:
        raise ValueError(f"Target document package '{pdf_path.name}' is empty (0 bytes).")

    print("\n" + "=" * 75)
    print("  ELEOS MEMBER 1: REAL-WORLD DOCUMENT INGESTION & TRUST SCORING")
    print("=" * 75)
    print(f"Target Document Package : {pdf_path.name}")
    print(f"Extraction Provider     : {provider.upper()}")
    print("-" * 75)

    # 1. Document Hashing & Anchoring
    file_hash = compute_file_sha256(pdf_path)
    file_size_kb = round(pdf_path.stat().st_size / 1024, 1)
    print(f"[1/5] Ingesting Document Package ({file_size_kb} KB)...")
    print(f"  [AUTHENTICITY] SHA-256 Digest: {file_hash}")

    # 2. Dual Provider Extraction
    print(f"[2/5] Running Multimodal Document Extraction via {provider.upper()}...")
    if provider.lower() == "aws":
        bundle = extract_ngo_document_package_aws(pdf_path)
    else:
        bundle = extract_ngo_document_package_gemini(pdf_path)

    ident = bundle.identity
    print(f"  [SUCCESS] Extracted Entity: {ident.ngo_name.value} ({ident.registration_type.value})")
    print(f"  [SUCCESS] PAN: {ident.pan.value} | Reg Number: {ident.registration_number.value}")
    if bundle.financials:
        f = bundle.financials[0]
        print(f"  [SUCCESS] Financial Year: {f.financial_year.value} | Total Income: INR {f.total_income.value:,.0f} | Total Exp: INR {f.total_expenditure.value:,.0f}")
        print(f"  [SUCCESS] Programme Exp: INR {f.programme_expenses.value:,.0f} | Admin Exp: INR {f.administrative_expenses.value:,.0f}")
        if f.udin and f.udin.value:
            print(f"  [SUCCESS] Auditor UDIN: {f.udin.value}")

    # 3. Zero-Trust Verification Engine
    print(f"[3/5] Executing Zero-Trust Verification Checks...")
    verification = run_zero_trust_verification(bundle)
    for finding in verification.get("findings", []):
        print(f"  [PASS] {finding}")
    for flag in verification.get("critical_flags", []):
        print(f"  [WARNING / DEDUCTION] {flag}")

    # 4. Feature Adaptation & Isolation Forest Inference
    print(f"[4/5] Adapting Canonical Bundle to Member 1 Feature Matrices & Isolation Forest...")
    m_row, p_row, f_row, o_row, df_fin_reports = canonical_bundle_to_member1_inputs(bundle, verification)
    anomaly_label = f_row.get("financial_anomaly_label", "Normal")
    anomaly_score = f_row.get("financial_anomaly_score", 0.0)
    print(f"  [ML INFERENCE] Isolation Forest Decision Score: {anomaly_score} -> Tier: {anomaly_label.upper()}")

    # 5. Deterministic Trustability Scoring Engine
    print(f"[5/5] Computing Deterministic 4-Dimension Trustability Assessment...")
    assessment = assess_single_ngo(
        ngo_id=str(m_row.get("ngo_id")),
        df_master=pd_series_to_df(m_row),
        df_profile=pd_series_to_df(p_row),
        df_fin_feats=pd_series_to_df(f_row),
        df_op_feats=pd_series_to_df(o_row),
        df_fin_reports=df_fin_reports,
        weights=DEFAULT_WEIGHTS
    )

    # Attach verification metadata & raw document hash
    assessment["raw_document_hashes"] = bundle.raw_document_hashes
    assessment["extraction_provider"] = bundle.extraction_provider
    assessment["verification_summary"] = {
        "status": verification.get("overall_verification_status"),
        "checks": verification.get("verification_checks")
    }

    # Save live assessment output
    out_file = OUTPUTS_DIR / f"live_assessment_{pdf_path.stem}.json"
    with open(out_file, "w", encoding="utf-8") as out_f:
        json.dump(assessment, out_f, indent=2)

    # Display Executive Summary
    print("=" * 75)
    print("  EXECUTIVE TRUSTABILITY ASSESSMENT RESULTS")
    print("=" * 75)
    print(f"Entity Name         : {assessment['ngo_name']}")
    print(f"Trustability Score  : {assessment['trustability_score']} / 100")
    print(f"Score Rating        : {assessment['score_interpretation']['label']}")
    print(f"Confidence Band     : {assessment['confidence_band']} (Confidence: {assessment['data_confidence']})")
    print("Dimension Breakdown :")
    print(f"  • Identity & Legal Registration   : {assessment['dimension_scores']['identity_legal']} / 100")
    print(f"  • Financial Transparency & Audits : {assessment['dimension_scores']['financial_transparency']} / 100")
    print(f"  • Operational Field Evidence      : {assessment['dimension_scores']['operational_evidence']} / 100")
    print(f"  • Statutory Data Completeness     : {assessment['dimension_scores']['data_completeness']} / 100")
    print(f"Anomaly Detection   : {assessment['financial_analysis']['financial_anomaly_label']} (Score: {assessment['financial_analysis']['financial_anomaly_score']})")
    print(f"Assessment Saved To : {out_file}")
    print("=" * 75 + "\n")

    return assessment


def pd_series_to_df(s):
    import pandas as pd
    return pd.DataFrame([s])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ELEOS Member 1: Real-World Document Ingestion & Scoring Pipeline")
    parser.add_argument("--input", type=str, required=True, help="Path to sample NGO PDF document package")
    parser.add_argument("--provider", type=str, default="gemini", choices=["gemini", "aws"], help="Extraction provider (gemini or aws)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Target document package not found at {input_path}")
    try:
        process_document_package(input_path, provider=args.provider)
    except Exception as e:
        print(f"\n[PIPELINE ERROR] Execution failed: {e}")
        sys.exit(1)

    process_document_package(input_path, provider=args.provider)

