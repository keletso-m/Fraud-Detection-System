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
