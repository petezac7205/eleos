"""
Master Flow Runner for Eleos Blockchain Platform
Executes all 11 lifecycle flows sequentially and prints a presentation-ready provenance report.
"""

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from blockchain.services.blockchain_service import BlockchainService

# Import all 11 modular flows
from scripts.flows.flow_01_ngo_compliance_anchor import run_flow as flow_01
from scripts.flows.flow_02_campaign_budget_freeze import run_flow as flow_02
from scripts.flows.flow_03_ai_scoring_snapshot import run_flow as flow_03
from scripts.flows.flow_04_donation_inflow_razorpay import run_flow as flow_04
from scripts.flows.flow_05_milestone_video_auditor_proof import run_flow as flow_05
from scripts.flows.flow_06_vendor_expense_outflow import run_flow as flow_06
from scripts.flows.flow_07_volunteer_credential import run_flow as flow_07
from scripts.flows.flow_08_whistleblower_dispute_flag import run_flow as flow_08
from scripts.flows.flow_09_transparent_refund import run_flow as flow_09
from scripts.flows.flow_10_daily_merkle_state_anchor import run_flow as flow_10
from scripts.flows.flow_11_merkle_tamper_detection import run_flow as flow_11


def run_master():
    print("=" * 80)
    print("        ELEOS MASTER BLOCKCHAIN LIFECYCLE FLOW RUNNER")
    print("          (Executing all 11 Modular Verification Flows)")
    print("=" * 80)

    blockchain_svc = BlockchainService()
    results = []

    flows = [
        ("Flow 01: NGO Legal Compliance", flow_01),
        ("Flow 02: Campaign & Budget Lock", flow_02),
        ("Flow 03: AI Score Snapshot", flow_03),
        ("Flow 04: Money In (Donation)", flow_04),
        ("Flow 05: Milestone Video Proof", flow_05),
        ("Flow 06: Money Out (Vendor Expense)", flow_06),
        ("Flow 07: Volunteer Impact Credential", flow_07),
        ("Flow 08: Whistleblower Flag", flow_08),
        ("Flow 09: Transparent Refund", flow_09),
        ("Flow 10: Daily Merkle State Anchor", flow_10),
        ("Flow 11: Tamper Proof Verification", flow_11),
    ]

    for idx, (name, flow_func) in enumerate(flows, 1):
        print(f"\n>>> EXECUTING [{idx}/11]: {name}...")
        try:
            res = flow_func()
            results.append((name, res, "SUCCESS"))
        except Exception as e:
            print(f"[-] Flow failed: {e}")
            results.append((name, str(e), "FAILED"))

    # Summary Table for Hackathon Demo / Presentation
    print("\n" + "=" * 80)
    print("                 HACKATHON LIVE DEMO PROVENANCE SUMMARY")
    print("=" * 80)
    for name, res, status in results:
        if isinstance(res, list):
            tx_links = " | ".join(blockchain_svc.get_explorer_url(tx) for tx in res)
            print(f"  * {name:<35} : [{status}] {tx_links}")
        elif isinstance(res, str) and res.startswith("0x") and len(res) == 66:
            print(f"  * {name:<35} : [{status}] {blockchain_svc.get_explorer_url(res)}")
        else:
            print(f"  * {name:<35} : [{status}] {res}")
    print("=" * 80)


if __name__ == "__main__":
    run_master()

