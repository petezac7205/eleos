"""
Unit Tests for Benchmark Fallback Hierarchy and Temporal Inflation Decay Engine
"""

from datetime import date, timedelta
from decimal import Decimal
import pytest
from unittest.mock import MagicMock

from database.models import CostBenchmark
from database.services.benchmark_service import BenchmarkService, benchmark_service


def test_temporal_decay_active_benchmark():
    """Test that an active (non-expired) benchmark undergoes zero decay/inflation."""
    base_cost = Decimal("100.00")
    future_expiry = date.today() + timedelta(days=180)
    
    adj_cost, mult, is_stale = BenchmarkService.calculate_temporal_decay(
        base_cost=base_cost,
        expiry_date=future_expiry
    )
    
    assert adj_cost == Decimal("100.00")
    assert mult == Decimal("1.0")
    assert is_stale is False


def test_temporal_decay_expired_benchmark():
    """Test that an expired benchmark compounds CPI inflation accurately."""
    base_cost = Decimal("100.00")
    # Expired 1 year ago (365.25 days)
    past_expiry = date.today() - timedelta(days=365)
    
    adj_cost, mult, is_stale = BenchmarkService.calculate_temporal_decay(
        base_cost=base_cost,
        expiry_date=past_expiry,
        annual_cpi_rate=Decimal("0.06")
    )
    
    assert is_stale is True
    assert mult > Decimal("1.05")  # ~1.06
    assert adj_cost > Decimal("105.00")


def test_fallback_hierarchy_district_match():
    """Test that District-level benchmark is matched first when available."""
    mock_db = MagicMock()
    mock_bm = CostBenchmark(
        category="nutrition",
        item="Meal (primary school)",
        unit="meal",
        unit_cost_mid=Decimal("5.45"),
        state="Tamil Nadu",
        district="Vellore",
        source_name="PM POSHAN FY25-26",
        authority_type="statutory_order",
        expiry_date=date.today() + timedelta(days=300)
    )
    mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_bm
    
    res = benchmark_service.find_benchmark_with_fallback(
        db=mock_db,
        category="nutrition",
        item_keyword="meal",
        state="Tamil Nadu",
        district="Vellore"
    )
    
    assert res.resolution == "district"
    assert res.is_stale is False
    assert res.adjusted_unit_cost_mid == Decimal("5.45")
    assert res.source_name == "PM POSHAN FY25-26"


def test_fallback_hierarchy_state_fallback():
    """Test that when district benchmark is missing, it falls back to State level."""
    mock_db = MagicMock()
    
    mock_state_bm = CostBenchmark(
        category="construction",
        item="Library room construction",
        unit="room",
        unit_cost_mid=Decimal("350000.00"),
        state="Maharashtra",
        district=None,
        source_name="MH PWD SoR",
        authority_type="statutory_order"
    )
    
    # 1st query (district) returns None, 2nd query (state) returns mock_state_bm
    mock_db.query.return_value.filter.return_value.filter.return_value.first.side_effect = [
        None,  # District miss
        mock_state_bm  # State hit
    ]
    
    res = benchmark_service.find_benchmark_with_fallback(
        db=mock_db,
        category="construction",
        item_keyword="library",
        state="Maharashtra",
        district="UnknownDistrict"
    )
    
    assert res.resolution == "state"
    assert res.adjusted_unit_cost_mid == Decimal("350000.00")
    assert res.source_name == "MH PWD SoR"


def test_fallback_hierarchy_national_fallback():
    """Test that when district and state benchmarks are missing, it falls back to National level."""
    mock_db = MagicMock()
    
    mock_national_bm = CostBenchmark(
        category="food",
        item="Wheat flour",
        unit="kg",
        unit_cost_mid=Decimal("30.00"),
        state=None,
        district=None,
        source_name="PDS retail",
        authority_type="statutory_order"
    )
    
    # District and State queries return None, National query returns mock_national_bm
    mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_national_bm
    
    res = benchmark_service.find_benchmark_with_fallback(
        db=mock_db,
        category="food",
        item_keyword="wheat",
        state="Rajasthan",
        district="Jaipur"
    )
    
    assert res.resolution in ("district", "state", "national")

