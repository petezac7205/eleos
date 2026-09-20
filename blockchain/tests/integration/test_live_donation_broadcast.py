"""
Post-Integration Live Tests: End-to-End Polygon Smart Contract Transaction Broadcast
Run with: pytest blockchain/tests/integration/test_live_donation_broadcast.py --live-polygon -v
"""

import uuid
import pytest
from blockchain.services.blockchain_service import BlockchainService
from blockchain.config import settings


@pytest.mark.live_polygon
def test_live_donation_recording_on_chain():
    """
    Broadcasts a real donation proof transaction to Polygon Amoy testnet
    if live credentials and contract address are configured.
    """
    if settings.is_simulation_mode():
        pytest.skip("Skipping live broadcast: CONTRACT_ADDRESS or BACKEND_PRIVATE_KEY is in placeholder mode.")

    service = BlockchainService()
    test_donation_id = uuid.uuid4()
    test_campaign_id = uuid.uuid4()

    tx_hash = service.record_donation(
        donation_id=test_donation_id,
        campaign_id=test_campaign_id,
        amount_inr=5.00,  # ₹5 test donation
        currency="INR"
    )

    assert tx_hash.startswith("0x")
    assert len(tx_hash) == 66

    # Verify transaction receipt on-chain
    receipt = service.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=45)
    assert receipt.status == 1
    assert receipt.blockNumber > 0

