"""
Phase 2 Test Suite: Scoring Engine, ML Anomaly Detection & Budget Feasibility Verification
Tests against live Supabase PostgreSQL database.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# Seed NGO UUIDs
HOPERELIEF_NGO_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ANNAPURNA_NGO_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
FLAGGED_NGO_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"

# Seed Campaign UUIDs
NEPAL_RELIEF_CAMPAIGN_ID = "10000000-0000-0000-0000-000000000001"
FLAGGED_CAMPAIGN_ID = "30000000-0000-0000-0000-000000000003"


def test_verify_item_pass():
    """Verify item priced within benchmark bounds returns pass / green."""
    payload = {
        "category": "food",
        "item_name": "Rice",
        "unit_cost": 32.0,
        "quantity": 500.0,
        "unit": "kg",
        "state": "Tamil Nadu",
        "district": "Chennai",
        "is_disaster_relief": True
    }
    resp = client.post("/api/scoring/verify-item", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["flag"] == "pass"
    assert data["safety_tier"] == "green"
    assert data["declared_unit_cost"] == 32.0
    assert data["benchmark_unit_cost_mid"] > 0
    assert "Within standard statutory benchmark range" in data["verdict"]


def test_verify_item_warning():
    """Verify item priced with moderate inflation returns warning / amber."""
    payload = {
        "category": "food",
        "item_name": "Rice",
        "unit_cost": 42.0,
        "quantity": 100.0,
        "unit": "kg",
        "state": "Tamil Nadu",
        "district": "Chennai",
        "is_disaster_relief": False
    }
    resp = client.post("/api/scoring/verify-item", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["flag"] == "warning"
    assert data["safety_tier"] == "amber"
    assert data["cost_ratio"] > 1.15


def test_verify_item_fail():
    """Verify item priced severely above benchmark returns fail / red."""
    payload = {
        "category": "food",
        "item_name": "Rice",
        "unit_cost": 150.0,
        "quantity": 100.0,
        "unit": "kg",
        "state": "Tamil Nadu",
        "district": "Chennai",
        "is_disaster_relief": False
    }
    resp = client.post("/api/scoring/verify-item", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["flag"] == "fail"
    assert data["safety_tier"] == "red"
    assert data["cost_ratio"] > 1.40


def test_list_benchmarks():
    """Verify listing and filtering of statutory cost benchmarks."""
    resp = client.get("/api/scoring/benchmarks?category=food&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    for item in data:
        assert item["category"].lower() == "food"
        assert item["unit_cost_mid"] is not None


def test_ngo_trust_score_verified():
    """Verify trust score computation for legitimate verified NGO."""
    resp = client.get(f"/api/scoring/ngo/{HOPERELIEF_NGO_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ngo_id"] == HOPERELIEF_NGO_ID
    assert data["overall_score"] >= 65
    assert data["overall_label"] in ["verified", "partially_verified"]
    assert "dimension_scores" in data
    assert "positive_evidence" in data
    assert len(data["positive_evidence"]) > 0


def test_ngo_trust_score_flagged():
    """Verify trust score computation for flagged suspicious NGO."""
    resp = client.get(f"/api/scoring/ngo/{FLAGGED_NGO_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ngo_id"] == FLAGGED_NGO_ID
    assert data["overall_score"] < 45
    assert data["overall_label"] == "high_risk"
    assert len(data["negative_evidence"]) > 0


def test_recalculate_ngo_score():
    """Verify on-demand recalculate endpoint."""
    resp = client.post(f"/api/scoring/ngo/{ANNAPURNA_NGO_ID}/recalculate")
    assert resp.status_code == 200
    data = resp.json()
    assert "assessment" in data
    assert data["assessment"]["overall_score"] > 0


def test_campaign_budget_check_legitimate():
    """Verify campaign budget audit on legitimate Nepal Relief campaign."""
    resp = client.post(f"/api/scoring/campaign/{NEPAL_RELIEF_CAMPAIGN_ID}/budget-check")
    assert resp.status_code == 200
    data = resp.json()
    assert data["campaign_id"] == NEPAL_RELIEF_CAMPAIGN_ID
    assert data["overall_score"] >= 60
    assert data["items_count"] > 0
    assert data["passed_items"] > 0


def test_campaign_budget_check_flagged():
    """Verify campaign budget audit detects severe overpricing on flagged campaign."""
    resp = client.post(f"/api/scoring/campaign/{FLAGGED_CAMPAIGN_ID}/budget-check")
    assert resp.status_code == 200
    data = resp.json()
    assert data["campaign_id"] == FLAGGED_CAMPAIGN_ID
    assert data["failed_items"] > 0
    assert data["campaign_safety_tier"] == "no_volunteers"

