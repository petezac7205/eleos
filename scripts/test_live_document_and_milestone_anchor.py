"""
Live Document & Milestone Proof On-Chain Anchoring Script
Anchors real legal documents from prac_doc/ and milestone evidence to Polygon Amoy.
"""

import sys
import uuid
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from blockchain.services.blockchain_service import BlockchainService, calculate_file_sha256
from database.connection import SessionLocal
from database.models import NGOProfile, Campaign


def run_document_and_milestone_anchor():
    print("=" * 70)
    print("  ELEOS ON-CHAIN DOCUMENT & MILESTONE EVIDENCE ANCHORING")
    print("=" * 70)

    blockchain_svc = BlockchainService()

    # Step 1: Check document from prac_doc
    doc_path = REPO_ROOT / "prac_doc" / "AKAHI" / "8.AAATA5079PE20214--12A-Approval.pdf"
    if not doc_path.exists():
        # Fallback to any PDF in prac_doc
        pdf_files = list((REPO_ROOT / "prac_doc").rglob("*.pdf"))
        if not pdf_files:
            print("[-] No PDF documents found in prac_doc/")
            return
        doc_path = pdf_files[0]

    print(f"\n[Step 1] Loading Document from prac_doc:")
    print(f"  - File Path : {doc_path.relative_to(REPO_ROOT)}")
    print(f"  - File Size : {doc_path.stat().st_size / 1024:.2f} KB")

    # Step 2: Compute SHA-256 hash of the real document
    doc_sha256 = calculate_file_sha256(doc_path)
    print(f"  - SHA-256   : {doc_sha256}")

    # Fetch or generate NGO ID
    db = SessionLocal()
    ngo = db.query(NGOProfile).first()
    ngo_id = ngo.id if ngo else uuid.uuid4()
    print(f"  - NGO ID    : {ngo_id}")

    # Step 3: Broadcast anchorDocument on Polygon Amoy
    print(f"\n[Step 2] Broadcasting 'DocumentAnchored' (12A Legal Certificate) to Polygon Amoy...")
    doc_tx_hash = blockchain_svc.anchor_document(
        ngo_id=ngo_id,
        doc_type="12a_certificate",
        file_hash=doc_sha256
    )
    doc_explorer_url = blockchain_svc.get_explorer_url(doc_tx_hash)
    print(f"  [OK] Document Anchored On-Chain!")
    print(f"  - TX Hash      : {doc_tx_hash}")
    print(f"  - Explorer URL : {doc_explorer_url}")

    # Step 4: Milestone Evidence Anchoring
    print(f"\n[Step 3] Simulating Milestone Video / Field Proof Anchoring...")
    campaign = db.query(Campaign).first()
    campaign_id = campaign.id if campaign else uuid.uuid4()

    # Milestone proof hash (e.g. hash of milestone delivery footage or GPS inspection)
    sample_evidence_payload = f"milestone_completion_proof:{campaign_id}:water_purification_installed"
    evidence_hash = hashlib.sha256(sample_evidence_payload.encode("utf-8")).hexdigest()

    print(f"  - Campaign ID   : {campaign_id}")
    print(f"  - Evidence Hash : {evidence_hash}")

    milestone_tx_hash = blockchain_svc.update_milestone(
        campaign_id=campaign_id,
        milestone_index=1,
        evidence_hash=evidence_hash,
        status="verified_milestone_1"
    )
    milestone_explorer_url = blockchain_svc.get_explorer_url(milestone_tx_hash)

    print(f"  [OK] Milestone Evidence Anchored On-Chain!")
    print(f"  - TX Hash      : {milestone_tx_hash}")
    print(f"  - Explorer URL : {milestone_explorer_url}")

    print("\n" + "=" * 70)
    print("  >>> ON-CHAIN ANCHORING COMPLETED SUCCESSFULLY! <<<")
    print("=" * 70)
    print(f"  * 12A Document Proof : {doc_explorer_url}")
    print(f"  * Milestone Proof    : {milestone_explorer_url}")
    print("=" * 70)

    db.close()


if __name__ == "__main__":
    run_document_and_milestone_anchor()

