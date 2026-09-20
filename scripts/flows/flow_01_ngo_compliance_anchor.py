"""
Flow 01: NGO Legal Compliance & Document Anchoring
Anchors real 12A and 80G tax exemption certificates from prac_doc/ onto Polygon Amoy.
"""

import sys
import uuid
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from blockchain.services.blockchain_service import BlockchainService, calculate_file_sha256
from database.connection import SessionLocal
from database.models import NGOProfile


def run_flow():
    print("=" * 70)
    print("  FLOW 01: NGO LEGAL COMPLIANCE & 12A/80G DOCUMENT ANCHORING")
    print("=" * 70)

    blockchain_svc = BlockchainService()
    db = SessionLocal()

    ngo = db.query(NGOProfile).first()
    ngo_id = ngo.id if ngo else uuid.uuid4()

    doc_12a = REPO_ROOT / "prac_doc" / "AKAHI" / "8.AAATA5079PE20214--12A-Approval.pdf"
    doc_80g = REPO_ROOT / "prac_doc" / "AKAHI" / "9.AAATA5079PF20214---80G-Approval.pdf"

    hash_12a = calculate_file_sha256(doc_12a) if doc_12a.exists() else hashlib.sha256(b"12a_cert").hexdigest()
    hash_80g = calculate_file_sha256(doc_80g) if doc_80g.exists() else hashlib.sha256(b"80g_cert").hexdigest()

    print(f"\n[1] Anchoring 12A Tax Exemption Certificate...")
    print(f"  - Document Path : {doc_12a.relative_to(REPO_ROOT) if doc_12a.exists() else 'sample'}")
    print(f"  - SHA-256 Hash  : {hash_12a}")
    tx1 = blockchain_svc.anchor_document(ngo_id=ngo_id, doc_type="12a_certificate", file_hash=hash_12a)
    print(f"  [OK] Anchored on Polygon: {blockchain_svc.get_explorer_url(tx1)}")

    print(f"\n[2] Anchoring 80G Approval Certificate...")
    print(f"  - SHA-256 Hash  : {hash_80g}")
    tx2 = blockchain_svc.anchor_document(ngo_id=ngo_id, doc_type="80g_approval", file_hash=hash_80g)
    print(f"  [OK] Anchored on Polygon: {blockchain_svc.get_explorer_url(tx2)}")

    print("\n" + "=" * 70)
    print("  >>> FLOW 01 COMPLETED SUCCESSFULLY! <<<")
    print("=" * 70)
    db.close()
    return [tx1, tx2]


if __name__ == "__main__":
    run_flow()

