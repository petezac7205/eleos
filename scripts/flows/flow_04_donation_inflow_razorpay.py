"""
Flow 04: Money In — Donation Inflow & Gateway Signature Binding
Records completed fiat/UPI donation and binds Razorpay HMAC-SHA256 receipt hash.
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


def run_flow(amount_inr: float = 5.0):
    print("=" * 70)
    print("  FLOW 04: MONEY IN — DONATION INFLOW & GATEWAY RECEIPT BINDING")
    print("=" * 70)

    blockchain_svc = BlockchainService()
    db = SessionLocal()

    campaign = db.query(Campaign).first()
    campaign_id = campaign.id if campaign else uuid.uuid4()
    donation_id = uuid.uuid4()

    # Razorpay Gateway HMAC Proof
    fake_order = f"order_{uuid.uuid4().hex[:10]}"
    fake_pay_id = f"pay_{uuid.uuid4().hex[:10]}"
    fake_signature = hashlib.sha256(f"{fake_order}|{fake_pay_id}".encode("utf-8")).hexdigest()
    gateway_receipt_hash = hashlib.sha256(f"{fake_order}:{fake_pay_id}:{fake_signature}".encode("utf-8")).hexdigest()

    print(f"\n[1] Recording Donation Inflow on Polygon Amoy...")
    print(f"  - Donation ID          : {donation_id}")
    print(f"  - Campaign ID          : {campaign_id}")
    print(f"  - Amount Ingested      : INR {amount_inr:,.2f} ({int(amount_inr * 100)} paise)")
    print(f"  - Razorpay Order ID    : {fake_order}")
    print(f"  - Gateway Receipt Hash : {gateway_receipt_hash}")

    tx = blockchain_svc.record_donation(
        donation_id=donation_id,
        campaign_id=campaign_id,
        amount_inr=amount_inr,
        gateway_receipt_hash=gateway_receipt_hash,
        currency="INR"
    )
    print(f"  [OK] Donation Anchored on Polygon: {blockchain_svc.get_explorer_url(tx)}")

    print("\n" + "=" * 70)
    print("  >>> FLOW 04 COMPLETED SUCCESSFULLY! <<<")
    print("=" * 70)
    db.close()
    return tx


if __name__ == "__main__":
    run_flow()

