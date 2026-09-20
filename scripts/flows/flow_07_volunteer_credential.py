"""
Flow 07: Volunteer Proof-of-Work & Service Credential
Issues an immutable on-chain proof of verified volunteer service hours.
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
    print("  FLOW 07: VOLUNTEER PROOF-OF-WORK & SERVICE CREDENTIAL")
    print("=" * 70)

    blockchain_svc = BlockchainService()
    db = SessionLocal()

    campaign = db.query(Campaign).first()
    campaign_id = campaign.id if campaign else uuid.uuid4()
    credential_id = uuid.uuid4()

    volunteer_identity_did = "did:eleos:volunteer:in_aadhaar_hash_8932fc"
    volunteer_hash = hashlib.sha256(volunteer_identity_did.encode("utf-8")).hexdigest()
    verified_hours = 12

    print(f"\n[1] Minting Volunteer Service Proof on Polygon Amoy...")
    print(f"  - Credential ID       : {credential_id}")
    print(f"  - Campaign ID         : {campaign_id}")
    print(f"  - Volunteer DID Hash  : {volunteer_hash}")
    print(f"  - Verified Hours      : {verified_hours} hours")

    tx = blockchain_svc.issue_volunteer_credential(
        credential_id=credential_id,
        campaign_id=campaign_id,
        volunteer_hash=volunteer_hash,
        hours=verified_hours
    )
    print(f"  [OK] Volunteer Proof Anchored: {blockchain_svc.get_explorer_url(tx)}")

    print("\n" + "=" * 70)
    print("  >>> FLOW 07 COMPLETED SUCCESSFULLY! <<<")
    print("=" * 70)
    db.close()
    return tx


if __name__ == "__main__":
    run_flow()

