"""
Eleos Full On-Chain Transparency Provenance Test Runner
Executes the complete 7-stage charity lifecycle on Polygon Amoy:
1. Legal Compliance Document Anchoring (12A / 80G / FCRA)
2. AI Trustability & Feasibility Score Snapshot
3. Campaign Itemized Budget Freeze
4. Donation Receipt Verification & Inflow (Money In)
5. Milestone Video / Field Proof Submission
6. Commercial Vendor Invoice & Outflow Verification (Money Out)
7. Volunteer Proof-of-Service Credential Issuance
"""

import sys
import uuid
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from blockchain.services.blockchain_service import BlockchainService, calculate_file_sha256
from database.connection import SessionLocal
from database.models import Campaign, NGOProfile, User


def run_complete_transparency_lifecycle():
    print("=" * 80)
    print("      ELEOS COMPLETE RADICAL TRANSPARENCY ON-CHAIN PROVENANCE")
    print("           (Money In -> Milestone Proof -> Money Out -> Impact)")
    print("=" * 80)

    blockchain_svc = BlockchainService()
    db = SessionLocal()

    campaign = db.query(Campaign).first()
    campaign_id = campaign.id if campaign else uuid.uuid4()
    ngo = db.query(NGOProfile).first()
    ngo_id = ngo.id if ngo else uuid.uuid4()

    print(f"\n[Context]")
    print(f"  - Target Campaign ID : {campaign_id}")
    print(f"  - NGO ID             : {ngo_id}")
    print(f"  - Smart Contract     : {blockchain_svc.contract_address}")

    # =========================================================================
    # STAGE 1: NGO Legal Document Anchoring (12A & 80G from prac_doc/)
    # =========================================================================
    print(f"\n" + "-" * 70)
    print("STAGE 1: Legal Compliance Document Anchoring (12A & 80G Certificates)")
    print("-" * 70)
    
    doc_12a_path = REPO_ROOT / "prac_doc" / "AKAHI" / "8.AAATA5079PE20214--12A-Approval.pdf"
    doc_80g_path = REPO_ROOT / "prac_doc" / "AKAHI" / "9.AAATA5079PF20214---80G-Approval.pdf"

    hash_12a = calculate_file_sha256(doc_12a_path) if doc_12a_path.exists() else hashlib.sha256(b"12a_sample").hexdigest()
    hash_80g = calculate_file_sha256(doc_80g_path) if doc_80g_path.exists() else hashlib.sha256(b"80g_sample").hexdigest()

    print(f"  - 12A Certificate Hash : {hash_12a}")
    tx_12a = blockchain_svc.anchor_document(ngo_id=ngo_id, doc_type="12a_approval", file_hash=hash_12a)
    print(f"  [OK] 12A Certificate Anchored: {blockchain_svc.get_explorer_url(tx_12a)}")

    print(f"  - 80G Certificate Hash : {hash_80g}")
    tx_80g = blockchain_svc.anchor_document(ngo_id=ngo_id, doc_type="80g_approval", file_hash=hash_80g)
    print(f"  [OK] 80G Certificate Anchored: {blockchain_svc.get_explorer_url(tx_80g)}")

    # =========================================================================
    # STAGE 2: AI Trustability & Feasibility Scoring Snapshot
    # =========================================================================
    print(f"\n" + "-" * 70)
    print("STAGE 2: AI Algorithmic Trustability Snapshot")
    print("-" * 70)
    
    ai_score_payload = {
        "ngo_id": str(ngo_id),
        "trustability_score": 91,
        "financial_health": 88,
        "governance_compliance": 95,
        "anomaly_flag": False
    }
    score_hash = hashlib.sha256(json.dumps(ai_score_payload, sort_keys=True).encode("utf-8")).hexdigest()
    print(f"  - AI Trust Score       : 91/100 (Explainable Model Snapshot)")
    print(f"  - Score Checksum Hash  : {score_hash}")
    tx_score = blockchain_svc.snapshot_score(ngo_id=ngo_id, score_hash=score_hash, overall_score=91, label="verified_tier_1")
    print(f"  [OK] Score Snapshot Anchored: {blockchain_svc.get_explorer_url(tx_score)}")

    # =========================================================================
    # STAGE 3: Itemized Budget Lock (Prevents stealth price alteration)
    # =========================================================================
    print(f"\n" + "-" * 70)
    print("STAGE 3: Campaign Budget Freeze & Itemized Unit Cost Lock")
    print("-" * 70)

    budget_items = [
        {"item": "Community Water Filtration Unit", "qty": 10, "unit_cost": 4500},
        {"item": "Installation & Plumbing", "qty": 10, "unit_cost": 500}
    ]
    budget_hash = hashlib.sha256(json.dumps(budget_items, sort_keys=True).encode("utf-8")).hexdigest()
    target_inr = 50000.0

    print(f"  - Target Budget Total  : INR {target_inr}")
    print(f"  - Budget Breakdown Hash: {budget_hash}")
    tx_budget = blockchain_svc.lock_campaign_budget(campaign_id=campaign_id, budget_items_hash=budget_hash, target_amount_inr=target_inr)
    print(f"  [OK] Budget Frozen On-Chain: {blockchain_svc.get_explorer_url(tx_budget)}")

    # =========================================================================
    # STAGE 4: Money In - Donation Inflow & Receipt Hash Binding
    # =========================================================================
    print(f"\n" + "-" * 70)
    print("STAGE 4: Donation Inflow (Money In Proof)")
    print("-" * 70)

    donation_id = uuid.uuid4()
    donation_amount = 5.0  # ₹5 test donation
    gw_receipt = f"rzp_order_{uuid.uuid4().hex[:8]}:pay_{uuid.uuid4().hex[:8]}:sig_verified"
    gw_hash = hashlib.sha256(gw_receipt.encode("utf-8")).hexdigest()

    print(f"  - Donation ID          : {donation_id}")
    print(f"  - Amount               : INR {donation_amount}")
    print(f"  - Gateway Receipt Hash : {gw_hash}")
    tx_donation = blockchain_svc.record_donation(
        donation_id=donation_id,
        campaign_id=campaign_id,
        amount_inr=donation_amount,
        gateway_receipt_hash=gw_hash
    )
    print(f"  [OK] Donation Recorded: {blockchain_svc.get_explorer_url(tx_donation)}")

    # =========================================================================
    # STAGE 5: Milestone Video / Field Proof Submission
    # =========================================================================
    print(f"\n" + "-" * 70)
    print("STAGE 5: Milestone Delivery Evidence (Field Video / Photo Proof)")
    print("-" * 70)

    milestone_video_payload = f"video_stream_ipfs_cid_QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx:{campaign_id}:m1"
    evidence_hash = hashlib.sha256(milestone_video_payload.encode("utf-8")).hexdigest()
    auditor_address = "0x0000000000000000000000000000000000000000"

    print(f"  - Milestone Index      : 1 (50% Completion - Water Units Installed)")
    print(f"  - Video/IPFS Proof Hash: {evidence_hash}")
    tx_milestone = blockchain_svc.update_milestone(
        campaign_id=campaign_id,
        milestone_index=1,
        evidence_hash=evidence_hash,
        attestation_signer=auditor_address,
        status="milestone_1_verified"
    )
    print(f"  [OK] Milestone Proof Anchored: {blockchain_svc.get_explorer_url(tx_milestone)}")

    # =========================================================================
    # STAGE 6: Money Out - Commercial Vendor Invoice & Expense Outflow
    # =========================================================================
    print(f"\n" + "-" * 70)
    print("STAGE 6: Commercial Vendor Expense & Invoice Outflow (Money Out)")
    print("-" * 70)

    vendor_gstin = "27AABCS1429B1ZB"
    vendor_gst_hash = hashlib.sha256(vendor_gstin.encode("utf-8")).hexdigest()
    vendor_invoice_hash = hashlib.sha256(b"vendor_tax_invoice_INV-2026-089.pdf").hexdigest()
    expense_amount = 25000.0

    print(f"  - Vendor GSTIN         : {vendor_gstin}")
    print(f"  - Invoice PDF Hash     : {vendor_invoice_hash}")
    print(f"  - Outflow Disbursed    : INR {expense_amount}")
    tx_expense = blockchain_svc.record_expense(
        campaign_id=campaign_id,
        milestone_index=1,
        amount_inr=expense_amount,
        vendor_gst=vendor_gst_hash,
        invoice_hash=vendor_invoice_hash
    )
    print(f"  [OK] Expense Recorded: {blockchain_svc.get_explorer_url(tx_expense)}")

    # =========================================================================
    # STAGE 7: Volunteer Proof-of-Work Credential
    # =========================================================================
    print(f"\n" + "-" * 70)
    print("STAGE 7: Volunteer Proof-of-Service Credential")
    print("-" * 70)

    credential_id = uuid.uuid4()
    volunteer_identity_hash = hashlib.sha256(b"volunteer_aadhaar_did_hash_xyz").hexdigest()
    service_hours = 12

    print(f"  - Volunteer DID Hash   : {volunteer_identity_hash}")
    print(f"  - Verified Hours       : {service_hours} hours")
    tx_volunteer = blockchain_svc.issue_volunteer_credential(
        credential_id=credential_id,
        campaign_id=campaign_id,
        volunteer_hash=volunteer_identity_hash,
        hours=service_hours
    )
    print(f"  [OK] Volunteer Credential Issued: {blockchain_svc.get_explorer_url(tx_volunteer)}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("  >>> COMPLETE 7-STAGE TRANSPARENCY PROVENANCE BROADCAST SUCCESSFUL! <<<")
    print("=" * 80)
    print(f"  1. 12A Legal Proof      : {blockchain_svc.get_explorer_url(tx_12a)}")
    print(f"  2. 80G Legal Proof      : {blockchain_svc.get_explorer_url(tx_80g)}")
    print(f"  3. AI Score Snapshot    : {blockchain_svc.get_explorer_url(tx_score)}")
    print(f"  4. Budget Lock Proof    : {blockchain_svc.get_explorer_url(tx_budget)}")
    print(f"  5. Money In (Donation)  : {blockchain_svc.get_explorer_url(tx_donation)}")
    print(f"  6. Milestone Video Proof: {blockchain_svc.get_explorer_url(tx_milestone)}")
    print(f"  7. Money Out (Vendor)   : {blockchain_svc.get_explorer_url(tx_expense)}")
    print(f"  8. Volunteer Credential : {blockchain_svc.get_explorer_url(tx_volunteer)}")
    print("=" * 80)

    db.close()


if __name__ == "__main__":
    run_complete_transparency_lifecycle()

