"""
Flow 10: Daily Cryptographic Merkle State Commitment
Constructs the binary Merkle tree from PostgreSQL and commits the root hash onto Polygon Amoy.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from blockchain.services.blockchain_service import BlockchainService
from blockchain.services.merkle_service import merkle_service
from database.connection import SessionLocal


def run_flow():
    print("=" * 70)
    print("  FLOW 10: DAILY CRYPTOGRAPHIC MERKLE STATE COMMITMENT")
    print("=" * 70)

    blockchain_svc = BlockchainService()
    db = SessionLocal()

    print(f"\n[1] Building Merkle Tree from Database State...")
    tree_data = merkle_service.build_daily_state_tree(db)
    merkle_root = tree_data["merkle_root"]
    record_count = tree_data["record_count"]
    timestamp = tree_data["timestamp"]

    print(f"  - Total Database Records : {record_count} items")
    print(f"  - Daily Merkle Root Hash : {merkle_root}")
    print(f"  - Timestamp (UTC)        : {datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()}")

    print(f"\n[2] Anchoring Daily State Root on Polygon Amoy...")
    tx = blockchain_svc.anchor_daily_state(
        merkle_root=merkle_root,
        date_timestamp=timestamp,
        record_count=record_count
    )
    print(f"  [OK] Daily Root Anchored: {blockchain_svc.get_explorer_url(tx)}")

    print("\n" + "=" * 70)
    print("  >>> FLOW 10 COMPLETED SUCCESSFULLY! <<<")
    print("=" * 70)
    db.close()
    return tx


if __name__ == "__main__":
    run_flow()

