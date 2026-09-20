"""
Flow 06: Money Out — Commercial Vendor Expense & Invoice Checksum
Records commercial contractor invoice PDF hash and Vendor GSTIN against a milestone.
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
    print("  FLOW 06: MONEY OUT — COMMERCIAL VENDOR INVOICE & EXPENSE")
    print("=" * 70)

    blockchain_svc = BlockchainService()
    db = SessionLocal()

    campaign = db.query(Campaign).first()
    campaign_id = campaign.id if campaign else uuid.uuid4()

    vendor_gstin = "27AABCS1429B1ZB"
    gst_hash = hashlib.sha256(vendor_gstin.encode("utf-8")).hexdigest()
    invoice_pdf_checksum = hashlib.sha256(b"commercial_tax_invoice_INV-2026-089_water_filters.pdf").hexdigest()
    expense_amount = 25000.0

    print(f"\n[1] Recording Commercial Expense Outflow on Polygon Amoy...")
    print(f"  - Campaign ID         : {campaign_id}")
    print(f"  - Milestone Index     : 1")
    print(f"  - Outflow Disbursed   : INR {expense_amount:,.2f}")
    print(f"  - Vendor GSTIN        : {vendor_gstin}")
    print(f"  - Vendor GSTIN Hash   : {gst_hash}")
    print(f"  - Invoice Checksum    : {invoice_pdf_checksum}")

    tx = blockchain_svc.record_expense(
        campaign_id=campaign_id,
        milestone_index=1,
        amount_inr=expense_amount,
        vendor_gst=gst_hash,
        invoice_hash=invoice_pdf_checksum
    )
    print(f"  [OK] Expense Recorded: {blockchain_svc.get_explorer_url(tx)}")

    print("\n" + "=" * 70)
    print("  >>> FLOW 06 COMPLETED SUCCESSFULLY! <<<")
    print("=" * 70)
    db.close()
    return tx


if __name__ == "__main__":
    run_flow()

