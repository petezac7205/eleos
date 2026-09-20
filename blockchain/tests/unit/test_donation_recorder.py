"""
Unit Tests for Donation Recorder Background Worker (Offline)
"""

import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from blockchain.workers.donation_recorder import record_donation_on_chain
from razorpay.services.redis_service import redis_service
from database.models import Donation


@pytest.mark.asyncio
async def test_record_donation_on_chain_success(sample_donation):
    """Test successful on-chain recording flow: DB update and Redis WebSocket notification."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = sample_donation
    mock_hash = "0x" + "11" * 32

    from blockchain.services.blockchain_service import blockchain_service

    with patch.object(blockchain_service, "record_donation", return_value=mock_hash) as mock_record, \
         patch.object(redis_service, "notify_donor", new_callable=AsyncMock) as mock_notify, \
         patch.object(redis_service, "broadcast_explorer", new_callable=AsyncMock) as mock_broadcast:

        tx_hash = await record_donation_on_chain(
            donation_id=sample_donation.id,
            campaign_id=sample_donation.campaign_id,
            amount=float(sample_donation.amount),
            donor_id=str(sample_donation.donor_id),
            campaign_title="Nepal Flood Relief 2026",
            db_session=mock_db
        )

        assert tx_hash == mock_hash
        assert mock_record.called
        
        # Verify DB model was updated
        assert sample_donation.blockchain_tx_hash == tx_hash
        assert sample_donation.blockchain_confirmed is True
        assert mock_db.commit.called

        # Verify WebSocket events were fired
        assert mock_notify.called
        assert mock_broadcast.called
        notify_args = mock_notify.call_args[1]
        assert notify_args["event_type"] == "blockchain_confirmed"
        assert notify_args["data"]["tx_hash"] == tx_hash


@pytest.mark.asyncio
async def test_record_donation_on_chain_anonymous_donor(sample_donation):
    """Test on-chain recording for anonymous donations (no user channel notification, but explorer feed broadcast)."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = sample_donation
    mock_hash = "0x" + "22" * 32

    from blockchain.services.blockchain_service import blockchain_service

    with patch.object(blockchain_service, "record_donation", return_value=mock_hash) as mock_record, \
         patch.object(redis_service, "notify_donor", new_callable=AsyncMock) as mock_notify, \
         patch.object(redis_service, "broadcast_explorer", new_callable=AsyncMock) as mock_broadcast:

        tx_hash = await record_donation_on_chain(
            donation_id=sample_donation.id,
            campaign_id=sample_donation.campaign_id,
            amount=float(sample_donation.amount),
            donor_id=None,  # Anonymous
            campaign_title="School Libraries",
            db_session=mock_db
        )

        assert tx_hash == mock_hash
        assert not mock_notify.called  # No donor channel
        assert mock_broadcast.called   # Public explorer feed still informed


@pytest.mark.asyncio
async def test_record_donation_on_chain_retry_success(sample_donation):
    """Test that transient failure triggers retry and succeeds on subsequent attempt."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = sample_donation

    from blockchain.services.blockchain_service import blockchain_service

    side_effects = [RuntimeError("RPC Timeout"), "0x" + "bb" * 32]

    with patch.object(blockchain_service, "record_donation", side_effect=side_effects) as mock_record, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

        tx_hash = await record_donation_on_chain(
            donation_id=sample_donation.id,
            campaign_id=sample_donation.campaign_id,
            amount=50.0,
            db_session=mock_db,
            max_retries=3
        )

        assert tx_hash == "0x" + "bb" * 32
        assert mock_record.call_count == 2
        assert mock_sleep.called


@pytest.mark.asyncio
async def test_record_donation_on_chain_exhausted_retries(sample_donation):
    """Test that persistent failure returns None when all retries are exhausted."""
    mock_db = MagicMock()

    from blockchain.services.blockchain_service import blockchain_service

    with patch.object(blockchain_service, "record_donation", side_effect=RuntimeError("Node Down")) as mock_record, \
         patch("asyncio.sleep", new_callable=AsyncMock):

        tx_hash = await record_donation_on_chain(
            donation_id=sample_donation.id,
            campaign_id=sample_donation.campaign_id,
            amount=50.0,
            db_session=mock_db,
            max_retries=3
        )

        assert tx_hash is None
        assert mock_record.call_count == 3


