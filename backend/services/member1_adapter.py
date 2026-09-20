"""
Member 1 Integration Adapter.
Bridges Member 1's Core Ingestion & Trustability Pipeline
(Gemini / AWS VLM, Zero-Trust Verifier, Canonical Schema, Isolation Forest)
with the FastAPI backend and Next.js frontend without altering core ML/verification logic.
"""

import os
import sys
import json
import uuid
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.run_document_pipeline import process_document_package

OUTPUTS_DIR = ROOT_DIR / "outputs"
ASSESSMENTS_FILE = OUTPUTS_DIR / "ngo_assessments.json"
UPLOADS_DIR = ROOT_DIR / "data" / "documents" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Map known seed UUIDs to Member 1 assessment keys for instant zero-latency demo loading
SEED_NGO_MAP = {
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa": "NGO_Clean",        # HopeRelief (High trust)
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb": "NGO_00002",        # Annapurna Trust / Uday Network (Verified)
    "cccccccc-cccc-cccc-cccc-cccccccccccc": "NGO_HighAdmin",    # Teach For Change
    "dddddddd-dddd-dddd-dddd-dddddddddddd": "NGO_Anomaly_Case", # GlobalAid (Suspicious Outlier)
}


def load_cached_assessment(ngo_key: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to find a pre-computed or live Member 1 assessment for an NGO key.
    """
    clean_key = str(ngo_key).strip()

    # 1. Check mapped seed UUID
    if clean_key in SEED_NGO_MAP:
        mapped_key = SEED_NGO_MAP[clean_key]
        cached = load_cached_assessment(mapped_key)
        if cached:
            return cached

    # 2. Check live output files
    candidate_files = [
        OUTPUTS_DIR / f"live_assessment_{clean_key}.json",
        OUTPUTS_DIR / f"{clean_key}_assessment.json",
        ROOT_DIR / "data" / "output" / "assessments" / f"{clean_key}_assessment.json",
    ]
    for p in candidate_files:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Member1Adapter] Error reading {p}: {e}")

    # 3. Check bulk assessments list (ngo_assessments.json)
    if ASSESSMENTS_FILE.exists():
        try:
            with open(ASSESSMENTS_FILE, "r", encoding="utf-8") as f:
                bulk = json.load(f)
                if isinstance(bulk, list):
                    for item in bulk:
                        if item.get("ngo_id") == clean_key or item.get("ngo_name") == clean_key:
                            return item
        except Exception as e:
            print(f"[Member1Adapter] Error reading bulk assessments: {e}")

    return None


def adapt_assessment_to_backend(assessment: Dict[str, Any], ngo: Optional[Any] = None) -> Dict[str, Any]:
    """
    Adapts Member 1 Section 47 assessment dictionary into the dual-key response shape
    expected by both the legacy backend and all frontend pages.
    """
    score_val = float(assessment.get("trustability_score", 0.0))
    rounded_score = int(round(score_val))
    dim_scores = assessment.get("dimension_scores", {})
    fin_analysis = assessment.get("financial_analysis", {})
    score_interp = assessment.get("score_interpretation", {})
    verif_summary = assessment.get("verification_summary", {})

    legal_val = float(dim_scores.get("identity_legal", 0.0))
    fin_val = float(dim_scores.get("financial_transparency", 0.0))
    op_val = float(dim_scores.get("operational_evidence", 0.0))
    comp_val = float(dim_scores.get("data_completeness", 0.0))

    anomaly_label = fin_analysis.get("financial_anomaly_label", "Normal")
    anomaly_score = fin_analysis.get("financial_anomaly_score", 0.0)

    # Risk tier determination
    if "outlier" in str(anomaly_label).lower() or score_val < 40:
        overall_label = "high_risk"
        risk_tier = "High Risk"
    elif score_val >= 80:
        overall_label = "verified"
        risk_tier = "Tier 1 Verified"
    elif score_val >= 60:
        overall_label = "partially_verified"
        risk_tier = "Partially Verified"
    else:
        overall_label = "under_review"
        risk_tier = "Requires Review"

    pos_evidence = assessment.get("positive_evidence", [])
    neg_evidence = assessment.get("negative_evidence", [])

    # Dual-key breakdown for frontend compatibility:
    # - /ngo/organisation expects { legal, financial, operational, completeness }
    # - /reviewer and scoring_service expect { identity_legal, financial_transparency, ... }
    breakdown = {
        "legal": round(legal_val, 1),
        "identity_legal": round(legal_val, 1),
        "financial": round(fin_val, 1),
        "financial_transparency": round(fin_val, 1),
        "operational": round(op_val, 1),
        "operational_evidence": round(op_val, 1),
        "completeness": round(comp_val, 1),
        "data_completeness": round(comp_val, 1),
        "data_confidence": float(assessment.get("data_confidence", 0.9)),
        "financial_anomaly_score": anomaly_score,
        "financial_anomaly_label": anomaly_label,
        "risk_tier": risk_tier,
        "positive_evidence": pos_evidence,
        "negative_evidence": neg_evidence,
        "statistical_findings": assessment.get("statistical_findings", [])
    }

    ngo_name = assessment.get("ngo_name") or (ngo.name if ngo else "Assessed NGO")
    ngo_id = str(ngo.id) if ngo else str(assessment.get("ngo_id", ""))

    return {
        "ngo_id": ngo_id,
        "ngo_name": ngo_name,
        "overall_score": rounded_score,
        "trust_score": rounded_score,
        "trustability_score": score_val,
        "overall_label": overall_label,
        "trust_label": risk_tier,
        "risk_tier": risk_tier,
        "data_confidence": float(assessment.get("data_confidence", 0.9)),
        "confidence_band": assessment.get("confidence_band", "High"),
        "dimension_scores": {
            "identity_legal": round(legal_val, 1),
            "financial_transparency": round(fin_val, 1),
            "operational_evidence": round(op_val, 1),
            "data_completeness": round(comp_val, 1)
        },
        "breakdown": breakdown,
        "score_interpretation": score_interp if score_interp else {
            "label": risk_tier,
            "description": "Evidence verified through Member 1 zero-trust pipeline."
        },
        "financial_analysis": fin_analysis,
        "positive_evidence": pos_evidence,
        "negative_evidence": neg_evidence,
        "statistical_findings": assessment.get("statistical_findings", []),
        "verification_summary": verif_summary,
        "extraction_provider": assessment.get("extraction_provider", "gemini"),
        "raw_document_hashes": assessment.get("raw_document_hashes", []),
        "is_member1_verified": True,
        "computed_at": datetime.utcnow().isoformat()
    }


def process_uploaded_document_package(
    file_bytes: bytes,
    filename: str,
    provider: str = "gemini",
    db: Optional[Any] = None,
    ngo_id: Optional[uuid.UUID] = None
) -> Dict[str, Any]:
    """
    Ingests an uploaded PDF file, runs Member 1's end-to-end pipeline,
    persists records to the Eleos database, and returns adapted assessment data.
    """
    if not file_bytes:
        raise ValueError("Uploaded document is empty (0 bytes).")

    # 1. Compute SHA-256 Digest
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ")
    target_path = UPLOADS_DIR / f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{safe_name}"

    with open(target_path, "wb") as f:
        f.write(file_bytes)

    # 2. Run Member 1 Document Pipeline
    assessment = process_document_package(target_path, provider=provider)

    # 3. Adapt for Backend/Frontend
    adapted = adapt_assessment_to_backend(assessment)

    # 4. If Database session and NGO profile provided, persist to database models
    if db is not None and ngo_id is not None:
        try:
            from database.models import Document, TrustabilityScore, NGOProfile
            ngo = db.query(NGOProfile).filter(NGOProfile.id == ngo_id).first()
            if ngo:
                adapted["ngo_name"] = ngo.name

            # Add / Update Document record
            doc = Document(
                id=uuid.uuid4(),
                ngo_id=ngo_id,
                doc_type="audit_report",
                file_url=f"/data/documents/uploads/{target_path.name}",
                file_hash=file_hash,
                file_size_bytes=len(file_bytes),
                fiscal_year="2024-25",
                ai_analysis=assessment,
                verified=True
            )
            db.add(doc)

            # Add / Update TrustabilityScore record
            score_rec = db.query(TrustabilityScore).filter(TrustabilityScore.ngo_id == ngo_id).first()
            if not score_rec:
                score_rec = TrustabilityScore(
                    id=uuid.uuid4(),
                    ngo_id=ngo_id,
                    identity_legal_score=int(round(adapted["dimension_scores"]["identity_legal"])),
                    financial_transparency_score=int(round(adapted["dimension_scores"]["financial_transparency"])),
                    operational_performance_score=int(round(adapted["dimension_scores"]["operational_evidence"])),
                    governance_score=int(round(adapted["dimension_scores"]["identity_legal"] * 0.9)),
                    data_completeness_score=int(round(adapted["dimension_scores"]["data_completeness"])),
                    overall_score=adapted["overall_score"],
                    overall_label=adapted["overall_label"],
                    breakdown=adapted["breakdown"],
                    computed_at=datetime.utcnow()
                )
                db.add(score_rec)
            else:
                score_rec.identity_legal_score = int(round(adapted["dimension_scores"]["identity_legal"]))
                score_rec.financial_transparency_score = int(round(adapted["dimension_scores"]["financial_transparency"]))
                score_rec.operational_performance_score = int(round(adapted["dimension_scores"]["operational_evidence"]))
                score_rec.governance_score = int(round(adapted["dimension_scores"]["identity_legal"] * 0.9))
                score_rec.data_completeness_score = int(round(adapted["dimension_scores"]["data_completeness"]))
                score_rec.overall_score = adapted["overall_score"]
                score_rec.overall_label = adapted["overall_label"]
                score_rec.breakdown = adapted["breakdown"]
                score_rec.computed_at = datetime.utcnow()

            db.commit()
        except Exception as db_err:
            print(f"[Member1Adapter] Error persisting to DB: {db_err}")
            if db:
                db.rollback()

    return adapted

