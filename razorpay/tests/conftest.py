"""
Pytest Fixtures for Razorpay Payment Tests
"""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from razorpay.main import app
from razorpay.services.razorpay_service import RazorpayService
from razorpay.services.redis_service import RedisService
from database.models import Campaign, Donation, User


@pytest.fixture
def mock_razorpay_service():
    """Custom configured RazorpayService instance with fixed test secrets."""
    return RazorpayService(
        key_id="rzp_test_samplekey123",
        key_secret="sample_secret_key_12345",
        webhook_secret="sample_webhook_secret_67890"
    )


@pytest.fixture
def test_client():
    """FastAPI TestClient for payment module endpoints."""
    return TestClient(app)


@pytest.fixture
def sample_campaign():
    """Sample Campaign model fixture."""
    return Campaign(
        id=uuid.UUID("10000000-0000-0000-0000-000000000001"),
        ngo_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        title="Nepal Flood Relief 2026",
        category="disaster_relief",
        target_amount=4700000.0,
        raised_amount=2300000.0,
        currency="INR",
        status="active"
    )


@pytest.fixture
def sample_donation(sample_campaign):
    """Sample initiated Donation model fixture."""
    return Donation(
        id=uuid.UUID("90000000-0000-0000-0000-000000000001"),
        donor_id=uuid.UUID("77777777-7777-7777-7777-777777777777"),
        campaign_id=sample_campaign.id,
        amount=500.0,
        currency="INR",
        payment_method="upi",
        payment_gateway_order_id="order_test_987654321",
        status="initiated",
        blockchain_confirmed=False,
        is_anonymous=False,
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def create_mock_db():
    """Factory fixture to create a mock DB session with row-level locking chained."""
    def _create(first_returns=None):
        db = MagicMock()
        filter_mock = db.query.return_value.filter.return_value
        filter_mock.with_for_update.return_value = filter_mock
        if first_returns is not None:
            if isinstance(first_returns, list):
                filter_mock.first.side_effect = first_returns
            else:
                filter_mock.first.return_value = first_returns
        return db
    return _create
