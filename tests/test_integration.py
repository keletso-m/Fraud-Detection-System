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

