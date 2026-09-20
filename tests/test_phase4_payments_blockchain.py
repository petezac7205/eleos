"""
Phase 4 Test Suite: Razorpay Payments, Universal Blockchain Logging & Donor Peer-Review Video Verification
Tests against live Supabase PostgreSQL database.
"""

import hmac
import hashlib
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import settings

client = TestClient(app)

NEPAL_CAMPAIGN_ID = "10000000-0000-0000-0000-000000000001"
DONOR_USER_ID = "77777777-7777-7777-7777-777777777777"


def get_auth_header(persona: str) -> dict:
    resp = client.post("/api/auth/demo-switch", json={"persona": persona})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_donation_initiation():
    """Verify Razorpay donation order creation and DB initiation."""
    donor_headers = get_auth_header("donor")
    payload = {
        "campaign_id": NEPAL_CAMPAIGN_ID,
        "amount": 1000.0,
        "currency": "INR",
        "donor_name": "Riya Sharma",
        "donor_email": "riya.sharma@example.com",
        "donor_phone": "+919876543216",
        "donor_message": "For relief supplies in Kathmandu Valley 🙏",
        "is_anonymous": False
    }
    resp = client.post("/api/donations/initiate", json=payload, headers=donor_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert "order_id" in data
    assert "donation_id" in data
    assert data["amount"] == 1000.0
    assert data["currency"] == "INR"


def test_donation_verification():
    """Verify payment signature verification and Polygon blockchain anchoring."""
    # 1. Initiate order
    payload = {
        "campaign_id": NEPAL_CAMPAIGN_ID,
        "amount": 500.0,
        "currency": "INR",
        "donor_name": "Riya Sharma",
        "donor_email": "riya.sharma@example.com",
        "donor_message": "Stay strong!",
        "is_anonymous": False
    }
    init_resp = client.post("/api/donations/initiate", json=payload)
    assert init_resp.status_code == 201
    order_data = init_resp.json()
    order_id = order_data["order_id"]
    payment_id = f"pay_{order_id.replace('order_', '')}"

    # 2. Compute HMAC-SHA256 signature
    msg = f"{order_id}|{payment_id}".encode("utf-8")
    secret = (settings.RAZORPAY_KEY_SECRET or "eleos_dummy_secret").encode("utf-8")
    signature = hmac.new(secret, msg, hashlib.sha256).hexdigest()

    # 3. Verify payment
    verify_payload = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature
    }
    verify_resp = client.post("/api/donations/verify", json=verify_payload)
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["status"] == "completed"
    assert verify_data["blockchain_confirmed"] is True
    assert verify_data["blockchain_tx_hash"] is not None


def test_campaign_blockchain_audit_trail():
    """Verify complete chronological transparency audit trail from Polygon."""
    resp = client.get(f"/api/explorer/campaign/{NEPAL_CAMPAIGN_ID}/audit-trail")
    assert resp.status_code == 200
    data = resp.json()
    assert data["campaign_id"] == NEPAL_CAMPAIGN_ID
    assert "audit_trail" in data
    assert len(data["audit_trail"]) > 0
    for event in data["audit_trail"]:
        assert "event" in event
        assert "tx_hash" in event
        assert "explorer_url" in event


def test_donor_as_reviewer_full_lifecycle():
    """
    Complete lifecycle test for Donor as Reviewer Video Milestone Verification:
    1. Charity uploads delivery video + wholesome note.
    2. Video is anchored on Polygon; invitations issued to qualifying donors (>= ₹500).
    3. Donor accesses review via magic token.
    4. Donor casts Thumbs Up vote.
    5. Vote is anchored on Polygon and community consensus updates.
    """
    # 1. Fetch milestone for Nepal Relief campaign
    camp_resp = client.get(f"/api/campaigns/{NEPAL_CAMPAIGN_ID}")
    assert camp_resp.status_code == 200
    milestones = camp_resp.json()["milestones"]
    assert len(milestones) > 0
    milestone_id = milestones[0]["id"]

    # 2. NGO Admin uploads delivery video
    ngo_headers = get_auth_header("ngo_admin")
    video_payload = {
        "video_url": "https://storage.eleos.app/milestone_videos/nepal_relief_food_delivery.mp4",
        "hearty_note_top": "Dear Donors, with your vital support, our first 5,000 grain kits arrived safely in Kathmandu Valley! Please review the delivery proof footage below.",
        "hearty_note_bottom": "Thank you for walking alongside our disaster relief response team. Your vote verifies this milestone on Polygon Amoy testnet.",
        "donor_threshold": 500.0
    }
    upload_resp = client.post(
        f"/api/donor-review/milestone/{milestone_id}/upload-video",
        json=video_payload,
        headers=ngo_headers
    )
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    assert upload_data["milestone_id"] == milestone_id
    assert upload_data["blockchain_tx_hash"] is not None
    assert upload_data["invitations_issued"] > 0

    magic_token = upload_data["invitations"][0]["magic_token"]

    # 3. Donor accesses review link
    inv_resp = client.get(f"/api/donor-review/invitation?token={magic_token}")
    assert inv_resp.status_code == 200
    inv_data = inv_resp.json()
    assert inv_data["video_url"] == video_payload["video_url"]
    assert inv_data["hearty_note_top"] == video_payload["hearty_note_top"]
    assert inv_data["milestone"]["id"] == milestone_id

    # 4. Donor casts 👍 Thumbs Up vote
    vote_payload = {
        "magic_token": magic_token,
        "vote": "thumbs_up",
        "feedback_note": "Clear footage showing the food packets delivered directly to affected families. Verified!"
    }
    vote_resp = client.post("/api/donor-review/vote", json=vote_payload)
    assert vote_resp.status_code == 200
    vote_data = vote_resp.json()
    assert vote_data["vote"] == "thumbs_up"
    assert vote_data["blockchain_tx_hash"] is not None
    assert vote_data["consensus"]["thumbs_up_count"] >= 1

    # 5. Check milestone consensus status
    consensus_resp = client.get(f"/api/donor-review/milestone/{milestone_id}/consensus")
    assert consensus_resp.status_code == 200
    cons_data = consensus_resp.json()
    assert cons_data["total_votes_received"] >= 1
    assert cons_data["thumbs_up_count"] >= 1

