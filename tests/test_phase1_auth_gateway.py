"""
Phase 1 Verification Test Suite: Unified Gateway & Auth Engine
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_gateway_health():
    """Verify backend health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Eleos" in data["gateway"]


def test_login_success():
    """Verify login with seed credentials."""
    payload = {
        "email": "riya.sharma@example.com",
        "password": "eleos@123"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "riya.sharma@example.com"
    assert data["user"]["role"] == "donor"


def test_login_invalid_password():
    """Verify login rejection with bad password."""
    payload = {
        "email": "riya.sharma@example.com",
        "password": "wrong_password_999"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_auth_me_protected():
    """Verify /api/auth/me works with valid JWT and fails without token."""
    # 1. Unauthenticated request
    unauth_resp = client.get("/api/auth/me")
    assert unauth_resp.status_code == 401

    # 2. Authenticated request
    login_resp = client.post("/api/auth/login", json={
        "email": "reviewer@eleos.app",
        "password": "eleos@123"
    })
    token = login_resp.json()["access_token"]

    auth_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert auth_resp.status_code == 200
    user_data = auth_resp.json()
    assert user_data["email"] == "reviewer@eleos.app"
    assert user_data["role"] == "reviewer"


def test_demo_persona_switch():
    """Verify 1-click demo persona generator for hackathons."""
    personas = ["donor", "ngo_admin", "reviewer", "volunteer", "admin"]
    for p in personas:
        resp = client.post("/api/auth/demo-switch", json={"persona": p})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["role"] in [p, "ngo_admin"]


def test_user_registration():
    """Verify user registration and token generation."""
    import uuid
    rand_id = uuid.uuid4().hex[:6]
    reg_payload = {
        "email": f"test.volunteer.{rand_id}@example.com",
        "password": "securepassword123",
        "name": f"Test Volunteer {rand_id}",
        "role": "volunteer"
    }
    resp = client.post("/api/auth/register", json=reg_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["email"] == reg_payload["email"]
    assert data["user"]["role"] == "volunteer"
    assert "access_token" in data

