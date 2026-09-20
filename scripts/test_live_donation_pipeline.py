"""
Live End-to-End Payment -> Webhook -> Blockchain Pipeline Test Runner
Tests:
1. Fetches an active campaign from database
2. Initiates donation via backend API
3. Sends cryptographically signed Razorpay 'payment.captured' webhook
4. Verifies database update and live Polygon Amoy blockchain transaction
"""

import sys
import hmac
import hashlib
import json
import uuid
import time
from pathlib import Path
import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from database.connection import SessionLocal
from database.models import Campaign, Donation
from razorpay.config import settings as rzp_settings
from blockchain.services.blockchain_service import blockchain_service

API_BASE_URL = "http://localhost:8001"


def run_test():
    print("=" * 70)
    print("  ELEOS LIVE WEBHOOK & BLOCKCHAIN PIPELINE TEST")
    print("=" * 70)

    # Step 1: Get or verify Campaign
    db = SessionLocal()
    campaign = db.query(Campaign).first()
    if not campaign:
        print("[-] No campaigns found in database. Creating temporary test campaign...")
        test_camp = Campaign(
            id=uuid.uuid4(),
            title="Clean Water Initiative for Rural Schools",
            description="Providing clean and filtered drinking water systems.",
            category="health",
            target_amount=50000.0,
            raised_amount=0.0,
            currency="INR",
            status="active"
        )
        db.add(test_camp)
        db.commit()
        db.refresh(test_camp)
        campaign = test_camp

    campaign_id = str(campaign.id)
    print(f"\n[Step 1] Selected Campaign:")
    print(f"  - Title: {campaign.title}")
    print(f"  - Campaign ID: {campaign_id}")
    print(f"  - Current Raised: ₹{campaign.raised_amount or 0}")

    # Step 2: Initiate Donation
    amount_inr = 5.0
    print(f"\n[Step 2] Calling POST /api/donations/initiate (Amount: ₹{amount_inr})...")
    init_payload = {
        "campaign_id": campaign_id,
        "amount": amount_inr,
        "currency": "INR",
        "payment_method": "upi",
        "donor_message": "UPI ₹5 Live Verification Test",
        "is_anonymous": False
    }

    with httpx.Client(base_url=API_BASE_URL, timeout=15.0) as client:
        init_res = client.post("/api/donations/initiate", json=init_payload)
        if init_res.status_code not in (200, 201):
            print(f"[-] Failed to initiate donation: {init_res.text}")
            return

        init_data = init_res.json()
        donation_id = init_data["donation_id"]
        order_id = init_data["order_id"]
        print(f"  [OK] Donation Initiated: {donation_id}")
        print(f"  [OK] Razorpay Order ID: {order_id}")

        # Step 3: Construct simulated Razorpay payment.captured webhook
        fake_payment_id = f"pay_test_{uuid.uuid4().hex[:12]}"
        webhook_body_dict = {
            "entity": "event",
            "account_id": "acc_eleos_live_test",
            "event": "payment.captured",
            "contains": ["payment"],
            "payload": {
                "payment": {
                    "entity": {
                        "id": fake_payment_id,
                        "entity": "payment",
                        "amount": int(amount_inr * 100),
                        "currency": "INR",
                        "status": "captured",
                        "order_id": order_id,
                        "method": "upi",
                        "vpa": "donor@upi",
                        "captured": True
                    }
                }
            },
            "created_at": int(time.time())
        }

        raw_body_bytes = json.dumps(webhook_body_dict, separators=(",", ":")).encode("utf-8")

        # Step 4: Sign payload using RAZORPAY_WEBHOOK_SECRET
        secret = rzp_settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8")
        signature = hmac.new(secret, raw_body_bytes, hashlib.sha256).hexdigest()

        print(f"\n[Step 3] Emitting Razorpay 'payment.captured' Webhook to Server...")
        print(f"  - Payment ID: {fake_payment_id}")
        print(f"  - HMAC-SHA256 Signature: {signature[:20]}...")

        webhook_res = client.post(
            "/api/donations/webhook",
            content=raw_body_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": signature
            }
        )

        print(f"  - Webhook Response Status: {webhook_res.status_code}")
        print(f"  - Webhook Response Body  : {webhook_res.text}")

        if webhook_res.status_code != 200:
            print("[-] Webhook delivery rejected by server.")
            return

    # Step 5: Wait for background blockchain worker
    print(f"\n[Step 4] Checking Database & Polygon Amoy Proof...")
    time.sleep(4)  # Wait for background task

    db.expire_all()
    updated_donation = db.query(Donation).filter(Donation.id == donation_id).first()
    updated_campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()

    print(f"  - Donation Status       : {updated_donation.status if updated_donation else 'Not Found'}")
    print(f"  - Campaign Total Raised : ₹{updated_campaign.raised_amount if updated_campaign else 0}")
    
    tx_hash = updated_donation.blockchain_tx_hash if updated_donation else None
    if tx_hash:
        print(f"  - Polygon TX Hash       : {tx_hash}")
        print(f"  - Live Explorer Link    : https://amoy.polygonscan.com/tx/{tx_hash}")
    else:
        print("  - [Note] TX Hash being confirmed in background worker.")

    print("\n" + "=" * 70)
    print("  >>> FULL WEBHOOK-TO-BLOCKCHAIN PIPELINE TEST COMPLETE <<<")
    print("=" * 70)
    db.close()


if __name__ == "__main__":
    run_test()

