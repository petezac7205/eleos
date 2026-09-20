"""
Unit Tests for Merkle Tree Service & Cryptographic State Proofs
"""

import json
import pytest
from web3 import Web3

from blockchain.services.merkle_service import (
    MerkleTree,
    hash_leaf,
    combine_hashes,
    keccak256_hash
)


def test_merkle_tree_single_leaf():
    leaf1 = hash_leaf({"id": "1", "amount": 100})
    tree = MerkleTree([leaf1])
    assert tree.root == leaf1
    assert tree.root_hex.startswith("0x")
    proof = tree.get_proof(0)
    assert isinstance(proof, list)
    assert MerkleTree.verify_proof(leaf1, proof, tree.root)


def test_merkle_tree_even_leaves():
    leaves = [
        hash_leaf({"id": str(i), "amount": i * 100})
        for i in range(4)
    ]
    tree = MerkleTree(leaves)

    assert len(tree.root) == 32
    for idx, leaf in enumerate(leaves):
        proof = tree.get_proof(idx)
        assert len(proof) == 2  # log2(4) = 2
        assert MerkleTree.verify_proof(leaf, proof, tree.root) is True


def test_merkle_tree_odd_leaves():
    leaves = [
        hash_leaf({"id": str(i), "amount": i * 50})
        for i in range(5)
    ]
    tree = MerkleTree(leaves)

    for idx, leaf in enumerate(leaves):
        proof = tree.get_proof(idx)
        assert MerkleTree.verify_proof(leaf, proof, tree.root) is True


def test_merkle_tree_tamper_detection():
    leaves = [
        hash_leaf({"id": "1", "amount": 500}),
        hash_leaf({"id": "2", "amount": 1000}),
        hash_leaf({"id": "3", "amount": 1500}),
        hash_leaf({"id": "4", "amount": 2000})
    ]
    tree = MerkleTree(leaves)
    proof_0 = tree.get_proof(0)

    # Legitimate leaf
    assert MerkleTree.verify_proof(leaves[0], proof_0, tree.root) is True

    # Tampered leaf (amount changed from 500 to 50000)
    tampered_leaf = hash_leaf({"id": "1", "amount": 50000})
    assert MerkleTree.verify_proof(tampered_leaf, proof_0, tree.root) is False


def test_sorted_pair_order_invariance():
    a = keccak256_hash(b"alpha")
    b = keccak256_hash(b"beta")

    # Sorted pair must produce exact same parent regardless of input order
    parent_ab = combine_hashes(a, b)
    parent_ba = combine_hashes(b, a)
    assert parent_ab == parent_ba

