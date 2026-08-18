"""fire through the full API stack
and test auth, rate limiting, protected routes, event submission,
incident workflow, entity history, and correlation"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.main import app

client = TestClient(app)

#helpers 

def register_user(username: str, password: str, role: str = "viewer"):
    return client.post("/auth/register", json={
        "username": username,
        "password": password,
        "role": role,
    })

def login_user(username: str, password: str) -> str | None:
    resp = client.post("/auth/login", json={
        "username": username,
        "password": password,
    })
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

ACTIVITY_PAYLOAD = {
    "username":      "alice",
    "ip_address":    "203.0.113.99",
    "timestamp":     "2024-11-01T02:15:00",
    "failed_logins": 8,
    "command":       "cat /etc/passwd",
}

TRANSACTION_PAYLOAD = {
    "account_id":      "alice",
    "amount":          50000.00,
    "currency":        "ZAR",
    "location":        "London",
    "last_location":   "Johannesburg",
    "device_id":       "device-new",
    "known_devices":   ["device-trusted"],
    "recent_tx_count": 5,
    "timestamp":       "2024-11-01T02:15:00",
    "username":        "alice",
    "ip_address":      "203.0.113.99",
}

# fixtures 
@pytest.fixture(scope="module")
def admin_token():
    register_user("test_admin", "adminpass123", "admin")
    token = login_user("test_admin", "adminpass123")
    assert token is not None
    return token


@pytest.fixture(scope="module")
def viewer_token():
    register_user("test_viewer", "viewerpass123", "viewer")
    token = login_user("test_viewer", "viewerpass123")
    assert token is not None
    return token

# make a real incident and return its ID for workflow test
@pytest.fixture(scope="module")
def incident_id(admin_token):
    resp = client.post(
        "/events/activity",
        json=ACTIVITY_PAYLOAD,
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    inc_id = resp.json().get("id")
    assert inc_id is not None
    return inc_id

# auth tests
class TestAuth:

    def test_register_success(self):
        resp = register_user("new_user_1", "password123", "viewer")
        assert resp.status_code == 201
        assert "created" in resp.json()["message"]

    def test_register_duplicate_username(self):
        register_user("duplicate_user", "password123")
        resp = register_user("duplicate_user", "password123")
        assert resp.status_code == 409

    def test_login_success(self):
        register_user("login_test_user", "password123", "viewer")
        resp = client.post("/auth/login", json={
            "username": "login_test_user",
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "viewer"

    def test_login_wrong_password(self):
        register_user("login_test_user2", "correctpass")
        resp = client.post("/auth/login", json={
            "username": "login_test_user2",
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self):
        resp = client.post("/auth/login", json={
            "username": "nobody",
            "password": "password",
        })
        assert resp.status_code == 40 

# protected route tests 
class TestProtectedRoutes:

    def test_activity_without_token_returns_401(self):
        resp = client.post("/events/activity", json=ACTIVITY_PAYLOAD)
        assert resp.status_code == 401

    def test_transaction_without_token_returns_401(self):
        resp = client.post("/events/transaction", json=TRANSACTION_PAYLOAD)
        assert resp.status_code == 401

    def test_incidents_without_token_returns_401(self):
        resp = client.get("/incidents/")
        assert resp.status_code == 401

    def test_viewer_cannot_submit_activity(self, viewer_token):
        resp = client.post(
            "/events/activity",
            json=ACTIVITY_PAYLOAD,
            headers=auth_header(viewer_token),
        )
        assert resp.status_code == 403

    def test_viewer_cannot_submit_transaction(self, viewer_token):
        resp = client.post(
            "/events/transaction",
            json=TRANSACTION_PAYLOAD,
            headers=auth_header(viewer_token),
        )
        assert resp.status_code == 403

    def test_viewer_can_read_incidents(self, viewer_token):
        resp = client.get(
            "/incidents/",
            headers=auth_header(viewer_token),
        )
        assert resp.status_code == 200

    def test_invalid_token_returns_401(self):
        resp = client.get(
            "/incidents/",
            headers={"Authorization": "Bearer totallynotavalidtoken"},
        )
        assert resp.status_code == 401



