"""
Unit tests for DonationService business logic and state management.
"""

import json
import uuid
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from razorpay.services.donation_service import donation_service
from razorpay.services.razorpay_service import razorpay_service
from razorpay.schemas.donation import DonationInitiateRequest, DonationVerifyRequest
from database.models import Campaign, Donation, User


def test_initiate_donation_success(sample_campaign):
    """Test standard donation initiation flow with database persistence."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = sample_campaign

    req = DonationInitiateRequest(
        campaign_id=sample_campaign.id,
        amount=250.0,
        currency="INR",
        is_anonymous=False,
        donor_message="Support our heroes"
    )

    res = donation_service.initiate_donation(db=mock_db, request=req)

    assert res.amount == 250.0
    assert res.amount_paise == 25000
    assert res.currency == "INR"
    assert res.status == "initiated"
    assert res.order_id.startswith("order_")
    assert mock_db.add.called
    assert mock_db.commit.called


def test_initiate_donation_campaign_not_found():
    """Test initiation failure when the campaign ID does not exist."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    req = DonationInitiateRequest(
        campaign_id=uuid.uuid4(),
        amount=100.0,
        currency="INR"
    )

    with pytest.raises(HTTPException) as exc_info:
        donation_service.initiate_donation(db=mock_db, request=req)

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


def test_verify_client_payment_success(create_mock_db, sample_campaign, sample_donation):
    """Test client-side payment verification and transition to completed status."""
    mock_db = create_mock_db([sample_donation, sample_campaign])

    with patch.object(razorpay_service, "verify_payment_signature", return_value=True):
        verify_req = DonationVerifyRequest(
            razorpay_order_id=sample_donation.payment_gateway_order_id,
            razorpay_payment_id="pay_test_12345",
            razorpay_signature="valid_sig"
        )

        res = donation_service.verify_client_payment(db=mock_db, verify_req=verify_req)

        assert res.verified is True
        assert res.status == "completed"
        assert sample_donation.status == "completed"
        assert sample_donation.payment_gateway_payment_id == "pay_test_12345"
        assert sample_donation.completed_at is not None
        assert mock_db.commit.called


def test_verify_client_payment_invalid_signature(sample_donation):
    """Test rejection when signature is invalid."""
    mock_db = MagicMock()

    with patch.object(razorpay_service, "verify_payment_signature", return_value=False):
        verify_req = DonationVerifyRequest(
            razorpay_order_id=sample_donation.payment_gateway_order_id,
            razorpay_payment_id="pay_test_12345",
            razorpay_signature="invalid_sig"
        )

        with pytest.raises(HTTPException) as exc_info:
            donation_service.verify_client_payment(db=mock_db, verify_req=verify_req)

        assert exc_info.value.status_code == 400
        assert "signature verification failed" in exc_info.value.detail.lower()


def test_webhook_payment_captured_idempotency(create_mock_db, sample_donation):
    """Test that duplicate webhook events for completed donations are handled idempotently."""
    sample_donation.status = "completed"
    mock_db = create_mock_db(sample_donation)

    raw_payload = json.dumps({
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_999",
                    "order_id": sample_donation.payment_gateway_order_id,
                    "amount": 50000
                }
            }
        }
    }).encode("utf-8")

    with patch.object(razorpay_service, "verify_webhook_signature", return_value=True):
        res = donation_service.process_webhook_event(
            db=mock_db,
            raw_body=raw_payload,
            signature="valid_webhook_sig"
        )

        assert res["status"] == "already_processed"
        assert res["donation_id"] == str(sample_donation.id)


def test_webhook_payment_failed(create_mock_db, sample_donation):
    """Test that payment.failed event marks donation as failed."""
    sample_donation.status = "initiated"
    mock_db = create_mock_db(sample_donation)

    raw_payload = json.dumps({
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_failed_111",
                    "order_id": sample_donation.payment_gateway_order_id
                }
            }
        }
    }).encode("utf-8")

    with patch.object(razorpay_service, "verify_webhook_signature", return_value=True):
        res = donation_service.process_webhook_event(
            db=mock_db,
            raw_body=raw_payload,
            signature="valid_webhook_sig"
        )

def test_initiate_donation_idempotency_cache(sample_campaign):
    """Test that submitting duplicate requests with the same idempotency_key returns cached order."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = sample_campaign

    idempotency_key = f"key_{uuid.uuid4().hex}"
    req = DonationInitiateRequest(
        campaign_id=sample_campaign.id,
        amount=100.0,
        currency="INR",
        idempotency_key=idempotency_key
    )

    with patch.object(razorpay_service, "create_order", wraps=razorpay_service.create_order) as spy_create:
        # First call: creates order
        res1 = donation_service.initiate_donation(db=mock_db, request=req)
        # Second call: uses cache
        res2 = donation_service.initiate_donation(db=mock_db, request=req)

        assert res1.order_id == res2.order_id
        assert res1.donation_id == res2.donation_id
        assert spy_create.call_count == 1  # Only 1 order created on gateway


def test_concurrent_verify_and_webhook_race_condition(create_mock_db, sample_campaign, sample_donation):
    """
    Test race condition scenario:
    Client verify and server webhook arrive simultaneously for the same donation.
    The campaign raised_amount must only be incremented ONCE.
    """
    initial_raised = sample_campaign.raised_amount
    mock_db = create_mock_db([
        sample_donation, sample_campaign,  # For client verify
        sample_donation, sample_campaign   # For webhook
    ])

    with patch.object(razorpay_service, "verify_payment_signature", return_value=True), \
         patch.object(razorpay_service, "verify_webhook_signature", return_value=True):

        # 1. First event (Client callback) completes payment
        verify_req = DonationVerifyRequest(
            razorpay_order_id=sample_donation.payment_gateway_order_id,
            razorpay_payment_id="pay_simultaneous_01",
            razorpay_signature="valid_sig"
        )
        res_verify = donation_service.verify_client_payment(db=mock_db, verify_req=verify_req)
        assert res_verify.verified is True
        assert sample_donation.status == "completed"

        # 2. Second event (Server webhook) arrives right after
        webhook_raw = json.dumps({
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_simultaneous_01",
                        "order_id": sample_donation.payment_gateway_order_id,
                        "amount": 50000
                    }
                }
            }
        }).encode("utf-8")

        res_webhook = donation_service.process_webhook_event(
            db=mock_db,
            raw_body=webhook_raw,
            signature="valid_webhook_sig"
        )

        # Webhook recognizes existing completion and skips re-incrementing
        assert res_webhook["status"] == "already_processed"
        # Total funds incremented by exactly 1 donation amount
        assert sample_campaign.raised_amount == initial_raised + sample_donation.amount


