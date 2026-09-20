"""
Eleos Merkle Tree Service
Constructs deterministic cryptographic Merkle trees from database state
and generates O(log N) proofs for trustless verification against Polygon Amoy.
"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID

from web3 import Web3
from sqlalchemy.orm import Session

from database.models import Donation, Campaign, Milestone, BudgetItem

logger = logging.getLogger("merkle_service")


def keccak256_hash(data: bytes) -> bytes:
    """Computes standard Keccak-256 hash using Web3."""
    return Web3.keccak(data)


def hash_leaf(record: Dict[str, Any]) -> bytes:
    """
    Serializes a database record dictionary into a canonical, sorted JSON string
    and computes its 32-byte Keccak-256 leaf hash.
    """
    canonical_json = json.dumps(record, sort_keys=True, default=str)
    return keccak256_hash(canonical_json.encode("utf-8"))


def combine_hashes(left: bytes, right: bytes) -> bytes:
    """
    Combines two 32-byte sibling hashes using sorted-pair ordering
    (compatible with OpenZeppelin and EleosRegistryV2.sol verifyDatabaseRecord).
    """
    if left <= right:
        return Web3.keccak(left + right)
    else:
        return Web3.keccak(right + left)


class MerkleTree:
    def __init__(self, leaves: List[bytes]):
        if not leaves:
            raise ValueError("Cannot construct Merkle tree with empty leaves list.")
        self.leaves = leaves
        self.layers: List[List[bytes]] = [leaves]
        self._build_tree()

    def _build_tree(self):
        current_layer = self.leaves
        while len(current_layer) > 1:
            next_layer = []
            for i in range(0, len(current_layer), 2):
                left = current_layer[i]
                if i + 1 < len(current_layer):
                    right = current_layer[i + 1]
                else:
                    # Duplicate last leaf if odd count
                    right = left
                parent = combine_hashes(left, right)
                next_layer.append(parent)
            self.layers.append(next_layer)
            current_layer = next_layer

    @property
    def root(self) -> bytes:
        """Returns the 32-byte Merkle root hash."""
        return self.layers[-1][0]

    @property
    def root_hex(self) -> str:
        """Returns 0x-prefixed 64-hex string of the Merkle root."""
        return "0x" + self.root.hex()

    def get_proof(self, index: int) -> List[str]:
        """
        Generates the O(log N) sibling hash path required to verify leaf at `index`.
        Returns a list of 0x-prefixed 64-hex strings.
        """
        if index < 0 or index >= len(self.leaves):
            raise IndexError("Leaf index out of bounds.")

        proof: List[str] = []
        current_idx = index

        for layer in self.layers[:-1]:
            is_right_child = (current_idx % 2 == 1)
            sibling_idx = current_idx - 1 if is_right_child else current_idx + 1

            if sibling_idx < len(layer):
                proof.append("0x" + layer[sibling_idx].hex())
            else:
                # Sibling was duplicated from self
                proof.append("0x" + layer[current_idx].hex())

            current_idx //= 2

        return proof

    @staticmethod
    def verify_proof(leaf: bytes, proof_hex: List[str], expected_root: bytes) -> bool:
        """
        Pure Python verification matching Solidity's verifyDatabaseRecord.
        """
        computed = leaf
        for p_hex in proof_hex:
            clean = p_hex.removeprefix("0x")
            element = bytes.fromhex(clean)
            computed = combine_hashes(computed, element)
        return computed == expected_root


class MerkleService:
    @staticmethod
    def serialize_donation(d: Donation) -> Dict[str, Any]:
        return {
            "entity": "donation",
            "id": str(d.id),
            "campaign_id": str(d.campaign_id),
            "donor_id": str(d.donor_id) if d.donor_id else None,
            "amount": float(d.amount),
            "currency": d.currency,
            "status": d.status,
            "order_id": d.payment_gateway_order_id,
            "created_at": d.created_at.isoformat() if d.created_at else None
        }

    @staticmethod
    def serialize_campaign(c: Campaign) -> Dict[str, Any]:
        return {
            "entity": "campaign",
            "id": str(c.id),
            "ngo_id": str(c.ngo_id) if c.ngo_id else None,
            "title": c.title,
            "target_amount": float(c.target_amount),
            "currency": c.currency,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }

    @staticmethod
    def serialize_milestone(m: Milestone) -> Dict[str, Any]:
        return {
            "entity": "milestone",
            "id": str(m.id),
            "campaign_id": str(m.campaign_id),
            "title": m.title,
            "status": m.status,
            "sort_order": m.sort_order,
            "target_date": m.target_date.isoformat() if m.target_date else None
        }

    def build_daily_state_tree(self, db: Session) -> Dict[str, Any]:
        """
        Extracts all canonical platform records from PostgreSQL and builds
        the daily cryptographic Merkle Tree state proof.
        """
        records_map: Dict[str, Dict[str, Any]] = {}
        leaves: List[bytes] = []
        record_keys: List[str] = []

        # 1. Fetch campaigns
        campaigns = db.query(Campaign).all()
        for c in campaigns:
            serialized = self.serialize_campaign(c)
            key = f"campaign:{c.id}"
            records_map[key] = serialized
            leaves.append(hash_leaf(serialized))
            record_keys.append(key)

        # 2. Fetch donations
        donations = db.query(Donation).all()
        for d in donations:
            serialized = self.serialize_donation(d)
            key = f"donation:{d.id}"
            records_map[key] = serialized
            leaves.append(hash_leaf(serialized))
            record_keys.append(key)

        # 3. Fetch milestones
        milestones = db.query(Milestone).all()
        for m in milestones:
            serialized = self.serialize_milestone(m)
            key = f"milestone:{m.id}"
            records_map[key] = serialized
            leaves.append(hash_leaf(serialized))
            record_keys.append(key)

        if not leaves:
            # Fallback genesis leaf if empty database
            genesis = {"entity": "genesis", "timestamp": datetime.now(timezone.utc).isoformat()}
            leaves.append(hash_leaf(genesis))
            record_keys.append("genesis:0")

        tree = MerkleTree(leaves)
        now_ts = int(datetime.now(timezone.utc).timestamp())

        # Generate individual proofs for fast lookup
        proofs = {}
        for idx, key in enumerate(record_keys):
            proofs[key] = {
                "leaf_hash": "0x" + leaves[idx].hex(),
                "proof": tree.get_proof(idx),
                "record": records_map.get(key, {})
            }

        return {
            "merkle_root": tree.root_hex,
            "record_count": len(leaves),
            "timestamp": now_ts,
            "proofs": proofs
        }


merkle_service = MerkleService()

