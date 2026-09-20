"""
End-to-End CLI Smoke Test: Razorpay Order -> Payment Signature -> Polygon Blockchain Broadcast
Runs the entire coupled payment-to-blockchain lifecycle without needing the frontend.
"""

import sys
import uuid
import asyncio
from pathlib import Path

# Ensure root directory is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from razorpay.services.razorpay_service import razorpay_service
from blockchain.services.blockchain_service import BlockchainService
from blockchain.config import settings


async def run_live_flow():
    print("=" * 70)
    print("  ELEOS LIVE END-TO-END DEMO FLOW (Razorpay -> Polygon Amoy)")
    print("=" * 70)
    
    # 1. Generate IDs and amount
    test_donation_id = uuid.uuid4()
    test_campaign_id = uuid.uuid4()
    amount_inr = 10.00  # \u20b910 test donation
    
    print(f"\n[Step 1] Initializing Donation Details:")
    print(f"  - Donation ID : {test_donation_id}")
    print(f"  - Campaign ID : {test_campaign_id}")
    print(f"  - Amount      : INR {amount_inr}")
    
    # 2. Create Razorpay Order
    print(f"\n[Step 2] Contacting Razorpay to create live/test Order...")
    order_res = razorpay_service.create_order(
        amount_inr=amount_inr,
        currency="INR",
        notes={
            "donation_id": str(test_donation_id),
            "campaign_id": str(test_campaign_id),
            "source": "e2e_cli_test"
        }
    )
    order_id = order_res["id"]
    print(f"  [OK] Razorpay Order Created: {order_id} ({order_res['amount']} paise)")
    
    # 3. Simulate Checkout & Sign Payment
    fake_payment_id = f"pay_test_{uuid.uuid4().hex[:12]}"
    print(f"\n[Step 3] Simulating Checkout (success@razorpay):")
    print(f"  - Payment ID  : {fake_payment_id}")
    
    # Generate cryptographic signature
    signature = razorpay_service.generate_test_signature(
        order_id=order_id,
        payment_id=fake_payment_id
    )
    print(f"  - Generated HMAC-SHA256 Signature : {signature[:20]}...")
    
    # Verify signature
    is_valid = razorpay_service.verify_payment_signature(
        order_id=order_id,
        payment_id=fake_payment_id,
        signature=signature
    )
    assert is_valid, "Signature verification failed!"
    print(f"  [OK] Payment Signature Cryptographically Verified!")
    
    # 4. Broadcast on Polygon Amoy
    print(f"\n[Step 4] Broadcasting 'DonationRecorded' Proof to Polygon Amoy...")
    print(f"  - Network RPC       : {settings.POLYGON_RPC_URL}")
    print(f"  - Contract Address  : {settings.CONTRACT_ADDRESS}")
    
    blockchain_svc = BlockchainService()
    tx_hash = blockchain_svc.record_donation(
        donation_id=test_donation_id,
        campaign_id=test_campaign_id,
        amount_inr=amount_inr,
        currency="INR"
    )
    
    explorer_url = blockchain_svc.get_explorer_url(tx_hash)
    
    print("\n" + "=" * 70)
    print("  >>> FULL END-TO-END FLOW COMPLETED SUCCESSFULLY! <<<")
    print("=" * 70)
    print(f"  * Donation ID     : {test_donation_id}")
    print(f"  * Razorpay Order  : {order_id}")
    print(f"  * Razorpay Payment: {fake_payment_id}")
    print(f"  * Polygon TX Hash : {tx_hash}")
    print(f"  * Live Explorer   : {explorer_url}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_live_flow())
