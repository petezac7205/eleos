"""
Eleos Daily Merkle State Anchoring Runner
Builds the daily cryptographic Merkle tree from PostgreSQL and commits
the Merkle Root onto Polygon Amoy blockchain.
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from database.connection import SessionLocal
from blockchain.services.merkle_service import merkle_service
from blockchain.services.blockchain_service import blockchain_service


def anchor_daily_state():
    print("=" * 75)
    print("      ELEOS DAILY CRYPTOGRAPHIC MERKLE STATE ANCHORING")
    print("       (Polygon Amoy Root Commitment for Database Immutability)")
    print("=" * 75)

    db = SessionLocal()
    try:
        # Step 1: Build the Merkle Tree from all current DB records
        print("\n[Step 1] Constructing Merkle Tree from Database Records...")
        tree_data = merkle_service.build_daily_state_tree(db)

        merkle_root = tree_data["merkle_root"]
        record_count = tree_data["record_count"]
        timestamp = tree_data["timestamp"]

        print(f"  - Total Records Processed : {record_count}")
        print(f"  - Timestamp (UTC)         : {datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()}")
        print(f"  - Daily Merkle Root Hash  : {merkle_root}")

        # Step 2: Anchor the Merkle Root on Polygon Amoy
        print("\n[Step 2] Broadcasting 'DailyStateAnchored' to Polygon Amoy...")
        tx_hash = blockchain_service.anchor_daily_state(
            merkle_root=merkle_root,
            date_timestamp=timestamp,
            record_count=record_count
        )

        explorer_url = blockchain_service.get_explorer_url(tx_hash)
        print(f"  [OK] Daily State Anchored On-Chain!")
        print(f"  - TX Hash      : {tx_hash}")
        print(f"  - Explorer URL : {explorer_url}")

        # Step 3: Verify a sample proof
        if tree_data["proofs"]:
            sample_key = list(tree_data["proofs"].keys())[0]
            sample_proof_data = tree_data["proofs"][sample_key]
            leaf_hash = sample_proof_data["leaf_hash"]
            proof_path = sample_proof_data["proof"]

            print(f"\n[Step 3] Verifying Sample Record Cryptographic Proof ({sample_key})...")
            is_valid = blockchain_service.verify_database_record(
                leaf_hash=leaf_hash,
                merkle_proof=proof_path,
                expected_root=merkle_root
            )
            print(f"  - Record Key       : {sample_key}")
            print(f"  - Proof Path Depth : {len(proof_path)} hops")
            print(f"  - Integrity Result : {'VALID (Authentic)' if is_valid else 'INVALID'}")

        print("\n" + "=" * 75)
        print("  >>> DAILY MERKLE STATE ANCHORING COMPLETED SUCCESSFULLY! <<<")
        print("=" * 75)
        return tx_hash

    finally:
        db.close()


if __name__ == "__main__":
    anchor_daily_state()

