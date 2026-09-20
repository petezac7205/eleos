"""
Integration tests for FastAPI Razorpay and Donation API Endpoints.
"""

import json
import uuid
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from razorpay.main import app
from razorpay.services.razorpay_service import razorpay_service
from database.connection import get_db
from database.models import Donation, Campaign


def test_api_health_check(test_client):
    """Test health check route."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "eleos-razorpay-payments"
    assert data["currency"] == "INR"


def test_api_initiate_donation_success(test_client, sample_campaign):
    """Test POST /api/donations/initiate."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = sample_campaign

    app.dependency_overrides[get_db] = lambda: mock_db

    payload = {
        "campaign_id": str(sample_campaign.id),
        "amount": 100.0,
        "payment_method": "upi",
        "currency": "INR",
        "is_anonymous": False
    }

    response = test_client.post("/api/donations/initiate", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 100.0
    assert data["amount_paise"] == 10000
    assert "order_id" in data
    assert data["status"] == "initiated"

    app.dependency_overrides.clear()


def test_api_initiate_donation_invalid_amount(test_client, sample_campaign):
    """Test POST /api/donations/initiate rejects amount below minimum 1 INR."""
    payload = {
        "campaign_id": str(sample_campaign.id),
        "amount": 0.50,  # Below 1.00 min
        "payment_method": "upi"
    }

    response = test_client.post("/api/donations/initiate", json=payload)
    assert response.status_code == 422  # Pydantic validation error


def test_api_verify_payment_success(test_client, create_mock_db, sample_donation, sample_campaign):
    """Test POST /api/donations/verify with valid signature."""
    mock_db = create_mock_db([sample_donation, sample_campaign])

    app.dependency_overrides[get_db] = lambda: mock_db

    with patch.object(razorpay_service, "verify_payment_signature", return_value=True):
        payload = {
            "razorpay_order_id": sample_donation.payment_gateway_order_id,
            "razorpay_payment_id": "pay_test_987654",
            "razorpay_signature": "valid_signature_token"
        }
        response = test_client.post("/api/donations/verify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is True
        assert data["status"] == "completed"
        assert data["payment_id"] == "pay_test_987654"

    app.dependency_overrides.clear()


def test_api_verify_payment_failure_on_invalid_sig(test_client):
    """Test POST /api/donations/verify with invalid signature."""
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch.object(razorpay_service, "verify_payment_signature", return_value=False):
        payload = {
            "razorpay_order_id": "order_bad_123",
            "razorpay_payment_id": "pay_bad_456",
            "razorpay_signature": "bad_sig"
        }
        response = test_client.post("/api/donations/verify", json=payload)
        assert response.status_code == 400
        assert "verification failed" in response.json()["detail"].lower()

    app.dependency_overrides.clear()


def test_api_webhook_missing_signature_header(test_client):
    """Test POST /api/donations/webhook rejects calls without X-Razorpay-Signature."""
    response = test_client.post("/api/donations/webhook", json={"event": "payment.captured"})
    assert response.status_code == 400
    assert "x-razorpay-signature" in response.json()["detail"].lower()


def test_api_get_donation_by_id(test_client, sample_donation):
    """Test GET /api/donations/{id}."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = sample_donation

    app.dependency_overrides[get_db] = lambda: mock_db

    app.dependency_overrides.clear()


def test_api_initiate_donation_with_idempotency_header(test_client, sample_campaign):
    """Test POST /api/donations/initiate with Idempotency-Key header."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = sample_campaign

    app.dependency_overrides[get_db] = lambda: mock_db

    idempotency_key = f"hdr_key_{uuid.uuid4().hex}"
    payload = {
        "campaign_id": str(sample_campaign.id),
        "amount": 150.0,
        "payment_method": "upi",
        "currency": "INR"
    }

    # First request
    res1 = test_client.post(
        "/api/donations/initiate",
        json=payload,
        headers={"Idempotency-Key": idempotency_key}
    )
    assert res1.status_code == 201
    data1 = res1.json()

    # Second duplicate request with same header
    res2 = test_client.post(
        "/api/donations/initiate",
        json=payload,
        headers={"Idempotency-Key": idempotency_key}
    )
    assert res2.status_code == 201
    data2 = res2.json()

    assert data1["order_id"] == data2["order_id"]
    assert data1["donation_id"] == data2["donation_id"]

    app.dependency_overrides.clear()


