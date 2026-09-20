"""
Flow 08: Permissionless Public Whistleblower Red-Flagging
Allows ANY public Web3 address to permanently log a dispute against a campaign without middleman approval.
"""

import sys
import uuid
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from blockchain.services.blockchain_service import BlockchainService
from database.connection import SessionLocal
from database.models import Campaign


def run_flow():
    print("=" * 70)
    print("  FLOW 08: PERMISSIONLESS PUBLIC WHISTLEBLOWER RED-FLAGGING")
    print("=" * 70)

    blockchain_svc = BlockchainService()
    db = SessionLocal()

    campaign = db.query(Campaign).first()
    campaign_id = campaign.id if campaign else uuid.uuid4()

    dispute_report_payload = f"whistleblower_evidence:campaign_{campaign_id}:vendor_substandard_equipment_detected"
    dispute_hash = hashlib.sha256(dispute_report_payload.encode("utf-8")).hexdigest()
    reason_code = "field_defect_dispute"

    print(f"\n[1] Submitting Permissionless Whistleblower Flag to Polygon Amoy...")
    print(f"  - Campaign ID         : {campaign_id}")
    print(f"  - Dispute Reason Code : {reason_code}")
    print(f"  - Evidence Checksum   : {dispute_hash}")
    print(f"  - Permission Needed   : ZERO (Open to all public wallets)")

    tx = blockchain_svc.flag_campaign(
        campaign_id=campaign_id,
        reason_code=reason_code,
        evidence_hash=dispute_hash
    )
    print(f"  [OK] Whistleblower Flag Mined on Polygon: {blockchain_svc.get_explorer_url(tx)}")

    print("\n" + "=" * 70)
    print("  >>> FLOW 08 COMPLETED SUCCESSFULLY! <<<")
    print("=" * 70)
    db.close()
    return tx


if __name__ == "__main__":
    run_flow()

