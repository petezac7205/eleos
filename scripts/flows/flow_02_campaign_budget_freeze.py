"""
Flow 02: Campaign Creation & Itemized Budget Freeze
Registers the approved campaign and freezes itemized unit-cost line items on Polygon Amoy.
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
from database.models import Campaign, NGOProfile


def run_flow():
    print("=" * 70)
    print("  FLOW 02: CAMPAIGN CREATION & ITEMIZED BUDGET FREEZE")
    print("=" * 70)

    blockchain_svc = BlockchainService()
    db = SessionLocal()

    campaign = db.query(Campaign).first()
    campaign_id = campaign.id if campaign else uuid.uuid4()
    ngo = db.query(NGOProfile).first()
    ngo_id = ngo.id if ngo else uuid.uuid4()
    target_amount = 50000.0

    print(f"\n[1] Registering Campaign on Polygon Amoy...")
    print(f"  - Campaign ID   : {campaign_id}")
    print(f"  - Target Budget : INR {target_amount:,.2f}")
    tx1 = blockchain_svc.create_campaign(
        campaign_id=campaign_id,
        ngo_id=ngo_id,
        target_amount_inr=target_amount
    )
    print(f"  [OK] Campaign Registered: {blockchain_svc.get_explorer_url(tx1)}")

    print(f"\n[2] Freezing Itemized Unit Costs On-Chain...")
    budget_breakdown = [
        {"item": "Community Water Filtration Unit", "qty": 10, "unit_cost": 4500},
        {"item": "Plumbing & Ground Fitting", "qty": 10, "unit_cost": 500}
    ]
    budget_hash = hashlib.sha256(json.dumps(budget_breakdown, sort_keys=True).encode("utf-8")).hexdigest()
    print(f"  - Unit Costs Breakdown : 10x Filter Units @ ₹4,500 + Plumbing @ ₹500")
    print(f"  - Budget Checksum Hash : {budget_hash}")
    tx2 = blockchain_svc.lock_campaign_budget(
        campaign_id=campaign_id,
        budget_items_hash=budget_hash,
        target_amount_inr=target_amount
    )
    print(f"  [OK] Budget Frozen On-Chain: {blockchain_svc.get_explorer_url(tx2)}")

    print("\n" + "=" * 70)
    print("  >>> FLOW 02 COMPLETED SUCCESSFULLY! <<<")
    print("=" * 70)
    db.close()
    return [tx1, tx2]


if __name__ == "__main__":
    run_flow()

