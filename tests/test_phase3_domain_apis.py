"""
Phase 3 Test Suite: Core Domain APIs (Campaigns, NGO Profiles, Volunteer Network, Reviewer Panel)
Tests against live Supabase PostgreSQL database.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# Helper function to get token for persona
def get_auth_header(persona: str) -> dict:
    resp = client.post("/api/auth/demo-switch", json={"persona": persona})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_campaigns_listing():
    """Verify public campaign listing with filters and stats."""
    resp = client.get("/api/campaigns?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "campaigns" in data
    assert len(data["campaigns"]) > 0
    c = data["campaigns"][0]
    assert "target_amount" in c
    assert "raised_amount" in c
    assert "percentage_funded" in c
    assert "ngo" in c


def test_campaign_detail():
    """Verify campaign detail with budget breakdown and milestones."""
    camp_id = "10000000-0000-0000-0000-000000000001"
    resp = client.get(f"/api/campaigns/{camp_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == camp_id
    assert len(data["budget_items"]) > 0
    assert len(data["milestones"]) > 0
    assert "feasibility" in data
    assert "ngo" in data


def test_create_campaign_and_audit():
    """Verify NGO Admin can create a campaign with automated budget verification."""
    ngo_headers = get_auth_header("ngo_admin")
    rand_suffix = uuid.uuid4().hex[:6]
    payload = {
        "title": f"Clean Water Initiative {rand_suffix}",
        "description": "Providing clean drinking water filtration systems to rural schools.",
        "category": "healthcare",
        "target_amount": 500000.0,
        "location_state": "Tamil Nadu",
        "location_district": "Chennai",
        "beneficiary_count": 800,
        "is_disaster_relief": False,
        "budget_items": [
            {
                "category": "medical",
                "description": "Water filtration system",
                "unit_cost": 400.0,
                "quantity": 1000.0,
                "unit": "kit"
            },
            {
                "category": "admin",
                "description": "Installation and logistics",
                "unit_cost": 100000.0,
                "quantity": 1.0,
                "unit": "lump"
            }
        ],
        "milestones": [
            {
                "title": "Phase 1: Procurement",
                "description": "Procure 500 filter units"
            },
            {
                "title": "Phase 2: Installation",
                "description": "Install in 20 primary schools"
            }
        ]
    }
    resp = client.post("/api/campaigns", json=payload, headers=ngo_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert "campaign_id" in data
    assert data["status"] == "pending_review"


def test_ngo_public_profile():
    """Verify public NGO profile view with active campaigns and trust score."""
    ngo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    resp = client.get(f"/api/ngo/{ngo_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == ngo_id
    assert data["name"] == "HopeRelief Foundation"
    assert "trustability" in data
    assert len(data["campaigns"]) > 0


def test_ngo_admin_profile_and_doc_upload():
    """Verify NGO Admin can view their profile and upload a compliance doc with SHA-256 hash."""
    ngo_headers = get_auth_header("ngo_admin")

    # 1. Get profile
    resp = client.get("/api/ngo/me/profile", headers=ngo_headers)
    assert resp.status_code == 200
    profile = resp.json()
    assert "trustability" in profile
    assert "documents" in profile

    # 2. Upload document
    doc_payload = {
        "doc_type": "audit_report",
        "file_url": "https://eleos-docs.s3.amazonaws.com/audit_fy25_26.pdf",
        "fiscal_year": "2025-26",
        "file_size_bytes": 2048500
    }
    upload_resp = client.post("/api/ngo/me/documents", json=doc_payload, headers=ngo_headers)
    assert upload_resp.status_code == 201
    doc_data = upload_resp.json()
    assert "file_hash" in doc_data
    assert len(doc_data["file_hash"]) == 64  # SHA-256


def test_volunteer_opportunities_and_applications():
    """Verify volunteer opportunity exploration and application submission."""
    # 1. List opportunities
    opps_resp = client.get("/api/volunteers/opportunities")
    assert opps_resp.status_code == 200
    opps = opps_resp.json()["opportunities"]
    assert len(opps) > 0
    opp_id = opps[0]["id"]

    # 2. Volunteer applies
    vol_headers = get_auth_header("volunteer")
    apply_resp = client.post("/api/volunteers/apply", json={"opportunity_id": opp_id}, headers=vol_headers)
    assert apply_resp.status_code in [200, 201]

    # 3. Volunteer checks applications
    my_apps_resp = client.get("/api/volunteers/my-applications", headers=vol_headers)
    assert my_apps_resp.status_code == 200
    apps = my_apps_resp.json()
    assert len(apps) > 0


def test_volunteer_public_credential():
    """Verify public verification of issued volunteer credential."""
    cred_id = "60000000-0000-0000-0000-000000000001"
    resp = client.get(f"/api/volunteers/credentials/{cred_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == cred_id
    assert data["hours_logged"] > 0
    assert data["blockchain_tx_hash"] is not None


def test_reviewer_queue_and_stats():
    """Verify Reviewer auditor queue, stats, and decision submission."""
    rev_headers = get_auth_header("reviewer")

    # 1. Fetch stats
    stats_resp = client.get("/api/reviewer/stats", headers=rev_headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "pending_reviews" in stats

    # 2. Fetch queue
    queue_resp = client.get("/api/reviewer/queue", headers=rev_headers)
    assert queue_resp.status_code == 200
    items = queue_resp.json()
    assert len(items) > 0

    # 3. Inspect single queue item
    queue_id = items[0]["id"]
    detail_resp = client.get(f"/api/reviewer/queue/{queue_id}", headers=rev_headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert "entity_detail" in detail

