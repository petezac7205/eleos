"""
Pytest Fixtures and Configuration for Blockchain Tests
Supports 2-tier testing: Offline Unit/Simulation Tests and Live Polygon Amoy Integration Tests.
"""

import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock

from database.models import Donation, Campaign


def pytest_addoption(parser):
    parser.addoption(
        "--live-polygon",
        action="store_true",
        default=False,
        help="Run live Polygon Amoy integration tests requiring RPC connectivity"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--live-polygon"):
        # If --live-polygon is passed, run all tests including live ones
        return
    skip_live = pytest.mark.skip(reason="Live Polygon tests require --live-polygon flag")
    for item in items:
        if "live_polygon" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture
def sample_donation_id():
    return uuid.UUID("90000000-0000-0000-0000-000000000001")


@pytest.fixture
def sample_campaign_id():
    return uuid.UUID("10000000-0000-0000-0000-000000000001")


@pytest.fixture
def sample_ngo_id():
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def sample_credential_id():
    return uuid.UUID("55555555-5555-5555-5555-555555555555")


@pytest.fixture
def sample_donation(sample_donation_id, sample_campaign_id):
    return Donation(
        id=sample_donation_id,
        donor_id=uuid.UUID("77777777-7777-7777-7777-777777777777"),
        campaign_id=sample_campaign_id,
        amount=500.0,
        currency="INR",
        payment_method="upi",
        payment_gateway_order_id="order_test_987654321",
        status="completed",
        blockchain_confirmed=False,
        is_anonymous=False,
        created_at=datetime.now(timezone.utc)
    )

