"""
Unit tests for Razorpay signature verification and order creation logic.
"""

import json
import pytest
from razorpay.services.razorpay_service import RazorpayService


def test_client_signature_verification_valid(mock_razorpay_service):
    """Verify that a valid HMAC-SHA256 payment signature passes verification."""
    order_id = "order_EKwxwAgItmmMnC"
    payment_id = "pay_G3bQZ4d5eF6g7H"
    valid_sig = mock_razorpay_service.generate_test_signature(order_id, payment_id)

    assert mock_razorpay_service.verify_payment_signature(order_id, payment_id, valid_sig) is True


def test_client_signature_verification_invalid(mock_razorpay_service):
    """Verify that a tampered/mismatched signature is rejected."""
    order_id = "order_EKwxwAgItmmMnC"
    payment_id = "pay_G3bQZ4d5eF6g7H"
    tampered_sig = "invalid_tampered_signature_hex_1234567890abcdef"

    assert mock_razorpay_service.verify_payment_signature(order_id, payment_id, tampered_sig) is False


def test_client_signature_verification_empty_inputs(mock_razorpay_service):
    """Verify that empty order ID, payment ID, or signature fails safely."""
    assert mock_razorpay_service.verify_payment_signature("", "pay_123", "sig") is False
    assert mock_razorpay_service.verify_payment_signature("order_123", "", "sig") is False
    assert mock_razorpay_service.verify_payment_signature("order_123", "pay_123", "") is False


def test_webhook_signature_verification_valid(mock_razorpay_service):
    """Verify that a valid webhook signature passes HMAC-SHA256 check."""
    payload = json.dumps({"event": "payment.captured", "test": True}).encode("utf-8")
    valid_webhook_sig = mock_razorpay_service.generate_test_webhook_signature(payload)

    assert mock_razorpay_service.verify_webhook_signature(payload, valid_webhook_sig) is True


def test_webhook_signature_verification_invalid(mock_razorpay_service):
    """Verify that a tampered webhook body fails signature verification."""
    payload = json.dumps({"event": "payment.captured"}).encode("utf-8")
    tampered_sig = "fake_signature_hex"

    assert mock_razorpay_service.verify_webhook_signature(payload, tampered_sig) is False


def test_order_creation_paise_conversion(mock_razorpay_service):
    """Verify that amount in INR is converted accurately to paise for Razorpay SDK."""
    order = mock_razorpay_service.create_order(amount_inr=500.0, currency="INR")
    assert order["amount"] == 50000  # 500 * 100 paise
    assert order["currency"] == "INR"
    assert order["id"].startswith("order_")
    assert order["status"] == "created"

