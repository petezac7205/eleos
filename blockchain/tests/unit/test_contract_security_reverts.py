"""
Unit Tests for Smart Contract Access Control and Security Reverts
Simulates an EVM node with EthereumTesterProvider, tests caller authorization,
unauthorized attacker reverts, and 2-step ownership state transitions.
"""

import uuid
from pathlib import Path
import pytest
from web3 import Web3, EthereumTesterProvider
from eth_tester import EthereumTester, PyEVMBackend
import solcx


@pytest.fixture(scope="module")
def compiled_contract():
    """Compiles EleosRegistry.sol with solcx 0.8.20."""
    solcx.set_solc_version("0.8.20")
    sol_file = Path(__file__).resolve().parent.parent.parent / "contracts" / "EleosRegistry.sol"
    
    compiled = solcx.compile_files(
        [sol_file],
        output_values=["abi", "bin"],
        solc_version="0.8.20"
    )
    
    contract_interface = next(
        v for k, v in compiled.items() if k.endswith(":EleosRegistry")
    )
    return {
        "abi": contract_interface["abi"],
        "bin": contract_interface["bin"]
    }


@pytest.fixture(scope="module")
def evm_env(compiled_contract):
    """Initializes local EVM tester with owner, attacker, and pending owner accounts."""
    eth_tester = EthereumTester(PyEVMBackend())
    w3 = Web3(EthereumTesterProvider(eth_tester))
    accounts = w3.eth.accounts
    owner = accounts[0]
    attacker = accounts[1]
    pending_owner = accounts[2]
    
    EleosRegistry = w3.eth.contract(abi=compiled_contract["abi"], bytecode=compiled_contract["bin"])
    tx_hash = EleosRegistry.constructor().transact({"from": owner})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    contract = w3.eth.contract(address=tx_receipt.contractAddress, abi=compiled_contract["abi"])
    
    return {
        "w3": w3,
        "contract": contract,
        "owner": owner,
        "attacker": attacker,
        "pending_owner": pending_owner
    }


def _dummy_bytes32(prefix: str = "1") -> bytes:
    return (prefix * 32)[:32].encode("utf-8")


# =========================================================================
# 1. OWNER-ONLY ACCESS CONTROL REVERTS (ATTACKER SCENARIOS)
# =========================================================================

def test_record_donation_unauthorized_revert(evm_env):
    """Verify attacker calling recordDonation() reverts with caller not authorized."""
    contract = evm_env["contract"]
    attacker = evm_env["attacker"]
    
    with pytest.raises(Exception, match="EleosRegistry: caller is not authorized owner"):
        contract.functions.recordDonation(
            _dummy_bytes32("d"),
            _dummy_bytes32("c"),
            _dummy_bytes32("g"),
            50000,
            "INR"
        ).transact({"from": attacker})


def test_update_milestone_unauthorized_revert(evm_env):
    """Verify attacker calling updateMilestone() reverts with caller not authorized."""
    contract = evm_env["contract"]
    attacker = evm_env["attacker"]
    zero_address = "0x0000000000000000000000000000000000000000"
    
    with pytest.raises(Exception, match="EleosRegistry: caller is not authorized owner"):
        contract.functions.updateMilestone(
            _dummy_bytes32("c"),
            1,
            _dummy_bytes32("e"),
            zero_address,
            "verified"
        ).transact({"from": attacker})


def test_snapshot_score_unauthorized_revert(evm_env):
    """Verify attacker calling snapshotScore() reverts with caller not authorized."""
    contract = evm_env["contract"]
    attacker = evm_env["attacker"]
    
    with pytest.raises(Exception, match="EleosRegistry: caller is not authorized owner"):
        contract.functions.snapshotScore(
            _dummy_bytes32("n"),
            _dummy_bytes32("s"),
            95,
            "verified"
        ).transact({"from": attacker})


def test_issue_volunteer_credential_unauthorized_revert(evm_env):
    """Verify attacker calling issueVolunteerCredential() reverts with caller not authorized."""
    contract = evm_env["contract"]
    attacker = evm_env["attacker"]
    
    with pytest.raises(Exception, match="EleosRegistry: caller is not authorized owner"):
        contract.functions.issueVolunteerCredential(
            _dummy_bytes32("v"),
            _dummy_bytes32("c"),
            _dummy_bytes32("h"),
            10
        ).transact({"from": attacker})


def test_create_campaign_unauthorized_revert(evm_env):
    """Verify attacker calling createCampaign() reverts with caller not authorized."""
    contract = evm_env["contract"]
    attacker = evm_env["attacker"]
    
    with pytest.raises(Exception, match="EleosRegistry: caller is not authorized owner"):
        contract.functions.createCampaign(
            _dummy_bytes32("c"),
            _dummy_bytes32("n"),
            10000000,
            "INR"
        ).transact({"from": attacker})


def test_anchor_document_unauthorized_revert(evm_env):
    """Verify attacker calling anchorDocument() reverts with caller not authorized."""
    contract = evm_env["contract"]
    attacker = evm_env["attacker"]
    
    with pytest.raises(Exception, match="EleosRegistry: caller is not authorized owner"):
        contract.functions.anchorDocument(
            _dummy_bytes32("n"),
            "80g_cert",
            _dummy_bytes32("f")
        ).transact({"from": attacker})


def test_record_expense_unauthorized_revert(evm_env):
    """Verify attacker calling recordExpense() reverts with caller not authorized."""
    contract = evm_env["contract"]
    attacker = evm_env["attacker"]
    
    with pytest.raises(Exception, match="EleosRegistry: caller is not authorized owner"):
        contract.functions.recordExpense(
            _dummy_bytes32("c"),
            1,
            2500000,
            _dummy_bytes32("g"),
            _dummy_bytes32("i")
        ).transact({"from": attacker})


def test_lock_campaign_budget_unauthorized_revert(evm_env):
    """Verify attacker calling lockCampaignBudget() reverts with caller not authorized."""
    contract = evm_env["contract"]
    attacker = evm_env["attacker"]
    
    with pytest.raises(Exception, match="EleosRegistry: caller is not authorized owner"):
        contract.functions.lockCampaignBudget(
            _dummy_bytes32("c"),
            _dummy_bytes32("b"),
            5000000
        ).transact({"from": attacker})


def test_flag_campaign_unauthorized_revert(evm_env):
    """Verify attacker calling flagCampaign() reverts with caller not authorized."""
    contract = evm_env["contract"]
    attacker = evm_env["attacker"]
    
    with pytest.raises(Exception, match="EleosRegistry: caller is not authorized owner"):
        contract.functions.flagCampaign(
            _dummy_bytes32("c"),
            "misleading_evidence",
            _dummy_bytes32("e")
        ).transact({"from": attacker})


def test_transfer_ownership_unauthorized_revert(evm_env):
    """Verify attacker calling transferOwnership() reverts with caller not authorized."""
    contract = evm_env["contract"]
    attacker = evm_env["attacker"]
    
    with pytest.raises(Exception, match="EleosRegistry: caller is not authorized owner"):
        contract.functions.transferOwnership(attacker).transact({"from": attacker})


# =========================================================================
# 2. OWNERSHIP VALIDATION & 2-STEP TRANSFER REVERTS
# =========================================================================

def test_transfer_ownership_zero_address_revert(evm_env):
    """Verify owner transferring to address(0) reverts."""
    contract = evm_env["contract"]
    owner = evm_env["owner"]
    zero_address = "0x0000000000000000000000000000000000000000"
    
    with pytest.raises(Exception, match="EleosRegistry: zero address not allowed"):
        contract.functions.transferOwnership(zero_address).transact({"from": owner})


def test_transfer_ownership_already_owner_revert(evm_env):
    """Verify owner transferring to current owner reverts."""
    contract = evm_env["contract"]
    owner = evm_env["owner"]
    
    with pytest.raises(Exception, match="EleosRegistry: already owner"):
        contract.functions.transferOwnership(owner).transact({"from": owner})


def test_accept_ownership_unauthorized_revert(evm_env):
    """Verify non-pending owner calling acceptOwnership() reverts."""
    contract = evm_env["contract"]
    owner = evm_env["owner"]
    attacker = evm_env["attacker"]
    pending_owner = evm_env["pending_owner"]
    
    # Initiate transfer to pending_owner
    contract.functions.transferOwnership(pending_owner).transact({"from": owner})
    assert contract.functions.pendingOwner().call() == pending_owner
    
    # Attacker tries to hijack by calling acceptOwnership
    with pytest.raises(Exception, match="EleosRegistry: caller is not pending owner"):
        contract.functions.acceptOwnership().transact({"from": attacker})


def test_ownership_transfer_full_lifecycle(evm_env):
    """Verify complete 2-step ownership lifecycle and subsequent permission transition."""
    contract = evm_env["contract"]
    old_owner = evm_env["owner"]
    new_owner = evm_env["pending_owner"]
    
    # Verify current owner
    assert contract.functions.owner().call() == old_owner
    
    # Transfer ownership
    contract.functions.transferOwnership(new_owner).transact({"from": old_owner})
    assert contract.functions.pendingOwner().call() == new_owner
    
    # Accept ownership as new_owner
    contract.functions.acceptOwnership().transact({"from": new_owner})
    assert contract.functions.owner().call() == new_owner
    assert contract.functions.pendingOwner().call() == "0x0000000000000000000000000000000000000000"
    
    # Old owner should now be rejected as unauthorized
    with pytest.raises(Exception, match="EleosRegistry: caller is not authorized owner"):
        contract.functions.recordDonation(
            _dummy_bytes32("d"),
            _dummy_bytes32("c"),
            _dummy_bytes32("g"),
            50000,
            "INR"
        ).transact({"from": old_owner})
        
    # New owner should succeed
    tx = contract.functions.recordDonation(
        _dummy_bytes32("d"),
        _dummy_bytes32("c"),
        _dummy_bytes32("g"),
        50000,
        "INR"
    ).transact({"from": new_owner})
    assert tx is not None
