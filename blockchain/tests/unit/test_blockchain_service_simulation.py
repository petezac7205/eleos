"""
Unit Tests for BlockchainService in Simulation Mode (Offline)
"""

import uuid
import pytest
from blockchain.services.blockchain_service import BlockchainService
from blockchain.config import BlockchainSettings


@pytest.fixture
def sim_service():
    """Returns an explicitly simulated BlockchainService instance."""
    return BlockchainService(
        rpc_url="http://localhost:8545",
        chain_id=80002,
        contract_address="0x0000000000000000000000000000000000000000",
        private_key="your_private_key_here"
    )


def test_simulation_mode_detection(sim_service):
    """Test that simulation mode is active when placeholder credentials are used."""
    assert sim_service.is_simulation_mode() is True


def test_record_donation_simulation(sim_service, sample_donation_id, sample_campaign_id):
    """Test record_donation returns a valid 64-hex simulated transaction hash."""
    tx_hash = sim_service.record_donation(
        donation_id=sample_donation_id,
        campaign_id=sample_campaign_id,
        amount_inr=500.0,
        gateway_receipt_hash="0x" + "aa" * 32,
        currency="INR"
    )
    assert isinstance(tx_hash, str)
    assert tx_hash.startswith("0x")
    assert len(tx_hash) == 66  # "0x" + 64 hex characters


def test_record_refund_simulation(sim_service, sample_donation_id, sample_campaign_id):
    """Test record_refund returns a valid 64-hex simulated transaction hash."""
    tx_hash = sim_service.record_refund(
        donation_id=sample_donation_id,
        campaign_id=sample_campaign_id,
        amount_inr=500.0,
        reason="campaign_cancelled"
    )
    assert isinstance(tx_hash, str)
    assert tx_hash.startswith("0x")
    assert len(tx_hash) == 66


def test_record_donation_deterministic_hash(sim_service, sample_donation_id, sample_campaign_id):
    """Test that identical inputs generate reproducible deterministic simulation hashes."""
    tx1 = sim_service.record_donation(sample_donation_id, sample_campaign_id, 250.0)
    tx2 = sim_service.record_donation(sample_donation_id, sample_campaign_id, 250.0)
    assert tx1 == tx2


def test_create_campaign_simulation(sim_service, sample_campaign_id, sample_ngo_id):
    """Test create_campaign simulation."""
    tx_hash = sim_service.create_campaign(
        campaign_id=sample_campaign_id,
        ngo_id=sample_ngo_id,
        target_amount_inr=4700000.0,
        currency="INR"
    )
    assert tx_hash.startswith("0x")
    assert len(tx_hash) == 66


def test_update_milestone_simulation(sim_service, sample_campaign_id):
    """Test update_milestone simulation."""
    evidence_hash = "a" * 64
    tx_hash = sim_service.update_milestone(
        campaign_id=sample_campaign_id,
        milestone_index=1,
        evidence_hash=evidence_hash,
        status="verified"
    )
    assert tx_hash.startswith("0x")
    assert len(tx_hash) == 66


def test_snapshot_score_simulation(sim_service, sample_ngo_id):
    """Test snapshot_score simulation."""
    score_hash = "b" * 64
    tx_hash = sim_service.snapshot_score(
        ngo_id=sample_ngo_id,
        score_hash=score_hash,
        overall_score=88,
        label="verified"
    )
    assert tx_hash.startswith("0x")
    assert len(tx_hash) == 66


def test_issue_volunteer_credential_simulation(sim_service, sample_credential_id, sample_campaign_id):
    """Test issue_volunteer_credential simulation."""
    volunteer_hash = "c" * 64
    tx_hash = sim_service.issue_volunteer_credential(
        credential_id=sample_credential_id,
        campaign_id=sample_campaign_id,
        volunteer_hash=volunteer_hash,
        hours=25
    )
    assert tx_hash.startswith("0x")
    assert len(tx_hash) == 66


def test_anchor_document_simulation(sim_service, sample_ngo_id):
    """Test anchor_document simulation."""
    file_hash = "d" * 64
    tx_hash = sim_service.anchor_document(
        ngo_id=sample_ngo_id,
        doc_type="80g_cert",
        file_hash=file_hash
    )
    assert tx_hash.startswith("0x")
    assert len(tx_hash) == 66


def test_record_expense_simulation(sim_service, sample_campaign_id):
    """Test record_expense simulation."""
    invoice_hash = "e" * 64
    tx_hash = sim_service.record_expense(
        campaign_id=sample_campaign_id,
        milestone_index=1,
        amount_inr=25000.0,
        vendor_gst="27AABCU9603R1ZM",
        invoice_hash=invoice_hash
    )
    assert tx_hash.startswith("0x")
    assert len(tx_hash) == 66


def test_lock_campaign_budget_simulation(sim_service, sample_campaign_id):
    """Test lock_campaign_budget simulation."""
    budget_hash = "f" * 64
    tx_hash = sim_service.lock_campaign_budget(
        campaign_id=sample_campaign_id,
        budget_items_hash=budget_hash,
        target_amount_inr=5000000.0
    )
    assert tx_hash.startswith("0x")
    assert len(tx_hash) == 66


def test_flag_campaign_simulation(sim_service, sample_campaign_id):
    """Test flag_campaign simulation."""
    evidence_hash = "1" * 64
    tx_hash = sim_service.flag_campaign(
        campaign_id=sample_campaign_id,
        reason_code="misleading_evidence",
        evidence_hash=evidence_hash
    )
    assert tx_hash.startswith("0x")
    assert len(tx_hash) == 66


def test_calculate_file_sha256_helper():
    """Test calculate_file_sha256 utility function."""
    from blockchain.services.blockchain_service import calculate_file_sha256
    raw_content = b"Eleos Transparency Proof 2026"
    h = calculate_file_sha256(raw_content)
    assert isinstance(h, str)
    assert len(h) == 64
    assert h == calculate_file_sha256("Eleos Transparency Proof 2026")


def test_explorer_url_generation(sim_service):
    """Test generating Polygonscan URL."""
    fake_tx = "0x" + "12" * 32
    url = sim_service.get_explorer_url(fake_tx)
    assert "amoy.polygonscan.com/tx/0x" in url
    assert fake_tx in url

