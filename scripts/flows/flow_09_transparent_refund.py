"""
Flow 09: Transparent Campaign Refund Execution
Logs on-chain donor refund execution if a project is canceled or fails audit verification.
"""

import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from blockchain.services.blockchain_service import BlockchainService
from database.connection import SessionLocal
from database.models import Campaign


def run_flow(refund_amount_inr: float = 5.0):
    print("=" * 70)
    print("  FLOW 09: TRANSPARENT CAMPAIGN REFUND EXECUTION")
    print("=" * 70)

    blockchain_svc = BlockchainService()
    db = SessionLocal()

    campaign = db.query(Campaign).first()
    campaign_id = campaign.id if campaign else uuid.uuid4()
    donation_id = uuid.uuid4()
    refund_reason = "milestone_unfulfilled_donor_refund"

    print(f"\n[1] Broadcasting Refund Proof on Polygon Amoy...")
    print(f"  - Donation ID         : {donation_id}")
    print(f"  - Campaign ID         : {campaign_id}")
    print(f"  - Refund Amount       : INR {refund_amount_inr:,.2f} ({int(refund_amount_inr * 100)} paise)")
    print(f"  - Refund Reason Code  : {refund_reason}")

    tx = blockchain_svc.record_refund(
        donation_id=donation_id,
        campaign_id=campaign_id,
        amount_inr=refund_amount_inr,
        reason=refund_reason
    )
    print(f"  [OK] Refund Event Anchored: {blockchain_svc.get_explorer_url(tx)}")

    print("\n" + "=" * 70)
    print("  >>> FLOW 09 COMPLETED SUCCESSFULLY! <<<")
    print("=" * 70)
    db.close()
    return tx


if __name__ == "__main__":
    run_flow()

