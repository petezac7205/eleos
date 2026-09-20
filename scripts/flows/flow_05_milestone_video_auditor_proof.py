"""
Flow 05: Milestone Delivery Evidence & Auditor Co-Signing
Anchors field delivery video/photos with independent certifying auditor wallet address.
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
    print("  FLOW 05: MILESTONE EVIDENCE & INDEPENDENT AUDITOR CO-SIGNING")
    print("=" * 70)

    blockchain_svc = BlockchainService()
    db = SessionLocal()

    campaign = db.query(Campaign).first()
    campaign_id = campaign.id if campaign else uuid.uuid4()

    # IPFS Video Evidence Proof
    ipfs_video_cid = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
    evidence_payload = f"ipfs://{ipfs_video_cid}:campaign_{campaign_id}:milestone_1_water_filters_installed"
    evidence_hash = hashlib.sha256(evidence_payload.encode("utf-8")).hexdigest()
    auditor_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"  # Independent Auditor Public Address

    print(f"\n[1] Submitting Verified Milestone Proof to Polygon Amoy...")
    print(f"  - Campaign ID         : {campaign_id}")
    print(f"  - Milestone Index     : 1 (50% Completion)")
    print(f"  - IPFS Video Checksum : {evidence_hash}")
    print(f"  - Auditor Co-Signer   : {auditor_address}")

    tx = blockchain_svc.update_milestone(
        campaign_id=campaign_id,
        milestone_index=1,
        evidence_hash=evidence_hash,
        attestation_signer=auditor_address,
        status="milestone_1_verified"
    )
    print(f"  [OK] Milestone Proof Anchored: {blockchain_svc.get_explorer_url(tx)}")

    print("\n" + "=" * 70)
    print("  >>> FLOW 05 COMPLETED SUCCESSFULLY! <<<")
    print("=" * 70)
    db.close()
    return tx


if __name__ == "__main__":
    run_flow()

