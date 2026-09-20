"""
Flow 03: Explainable AI Algorithmic Scoring Snapshot
Commits mathematical snapshots of AI Trustability and Feasibility scores onto Polygon Amoy.
"""

import sys
import uuid
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from blockchain.services.blockchain_service import BlockchainService
from database.connection import SessionLocal
from database.models import NGOProfile


def run_flow():
    print("=" * 70)
    print("  FLOW 03: EXPLAINABLE AI SCORING SNAPSHOT")
    print("=" * 70)

    blockchain_svc = BlockchainService()
    db = SessionLocal()

    ngo = db.query(NGOProfile).first()
    ngo_id = ngo.id if ngo else uuid.uuid4()

    # Explainable AI Feature Payload
    ai_score_details = {
        "ngo_id": str(ngo_id),
        "overall_trust_score": 91,
        "financial_transparency_score": 88,
        "governance_compliance_score": 95,
        "budget_anomaly_detected": False,
        "timestamp": "2026-09-18T12:00:00Z"
    }

    score_checksum = hashlib.sha256(json.dumps(ai_score_details, sort_keys=True).encode("utf-8")).hexdigest()

    print(f"\n[1] Anchoring AI Trust Score Snapshot...")
    print(f"  - NGO ID              : {ngo_id}")
    print(f"  - AI Trust Score      : 91/100 (Tier 1 Verified)")
    print(f"  - Explainability Hash : {score_checksum}")

    tx = blockchain_svc.snapshot_score(
        ngo_id=ngo_id,
        score_hash=score_checksum,
        overall_score=91,
        label="tier_1_verified"
    )
    print(f"  [OK] Snapshot Anchored on Polygon: {blockchain_svc.get_explorer_url(tx)}")

    print("\n" + "=" * 70)
    print("  >>> FLOW 03 COMPLETED SUCCESSFULLY! <<<")
    print("=" * 70)
    db.close()
    return tx


if __name__ == "__main__":
    run_flow()

