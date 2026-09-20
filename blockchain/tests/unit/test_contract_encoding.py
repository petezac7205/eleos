"""
Unit Tests for Contract Encoding, Hashing, and ABI Validation (Offline)
"""

import uuid
import json
from pathlib import Path
import pytest

from blockchain.services.blockchain_service import uuid_to_bytes32, bytes32_to_hex, blockchain_service


def test_uuid_to_bytes32_from_uuid_object():
    """Test converting standard python UUID object to 32 bytes."""
    u = uuid.UUID("90000000-0000-0000-0000-000000000001")
    b32 = uuid_to_bytes32(u)
    assert isinstance(b32, bytes)
    assert len(b32) == 32
    assert b32[:16] == u.bytes
    assert b32[16:] == b"\x00" * 16


def test_uuid_to_bytes32_from_uuid_string():
    """Test converting string UUID representation to 32 bytes."""
    raw_str = "10000000-0000-0000-0000-000000000001"
    b32 = uuid_to_bytes32(raw_str)
    assert len(b32) == 32
    assert b32 == uuid_to_bytes32(uuid.UUID(raw_str))


def test_uuid_to_bytes32_from_64_hex_hash():
    """Test converting 64-character SHA-256 hex string to 32 bytes."""
    sample_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    b32 = uuid_to_bytes32(sample_hash)
    assert len(b32) == 32
    assert b32.hex() == sample_hash


def test_uuid_to_bytes32_from_raw_bytes():
    """Test converting raw bytes to 32 bytes."""
    raw = b"\xaa" * 16
    b32 = uuid_to_bytes32(raw)
    assert len(b32) == 32
    assert b32[:16] == raw
    assert b32[16:] == b"\x00" * 16


def test_bytes32_to_hex_formatting():
    """Test 0x-prefixed 64-hex string representation."""
    b32 = b"\x01" * 32
    hex_str = bytes32_to_hex(b32)
    assert hex_str.startswith("0x")
    assert len(hex_str) == 66  # "0x" + 64 hex chars
    assert hex_str == "0x" + "01" * 32


def test_abi_artifact_structure():
    """Verify that EleosRegistry ABI defines all 5 required events and public methods."""
    abi_path = Path(__file__).resolve().parent.parent.parent / "abi" / "EleosRegistry.json"
    assert abi_path.exists()

    with open(abi_path, "r", encoding="utf-8") as f:
        artifact = json.load(f)

    abi = artifact.get("abi", artifact)
    event_names = {item["name"] for item in abi if item.get("type") == "event"}
    function_names = {item["name"] for item in abi if item.get("type") == "function"}

    # Events
    assert "DonationRecorded" in event_names
    assert "DonationRefunded" in event_names
    assert "MilestoneUpdated" in event_names
    assert "ScoreSnapshot" in event_names
    assert "VolunteerCredential" in event_names
    assert "CampaignCreated" in event_names
    assert "DocumentAnchored" in event_names
    assert "ExpenseRecorded" in event_names
    assert "CampaignBudgetLocked" in event_names
    assert "CampaignFlagged" in event_names
    assert "OwnershipTransferStarted" in event_names
    assert "OwnershipTransferred" in event_names

    # Public functions
    assert "recordDonation" in function_names
    assert "recordRefund" in function_names
    assert "updateMilestone" in function_names
    assert "snapshotScore" in function_names
    assert "issueVolunteerCredential" in function_names
    assert "createCampaign" in function_names
    assert "anchorDocument" in function_names
    assert "recordExpense" in function_names
    assert "lockCampaignBudget" in function_names
    assert "flagCampaign" in function_names
    assert "transferOwnership" in function_names
    assert "acceptOwnership" in function_names
    assert "pendingOwner" in function_names

