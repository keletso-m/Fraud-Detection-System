""" detectspatterns across multiple incidents """
import json
import logging
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger("sentinel.correlator")

ROOT    = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "incidents.db"

WINDOW_MINUTES = 60
MIN_INCIDENTS  = 2  # minimum incidents to form a correlation group

SEVERITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

# public interface
#run all correlation rules and return grouped results
def correlate() -> list[dict]:
    incidents = _fetch_recent()
    if not incidents:
        return []

    results = []
    results += _correlate_by_user(incidents)
    results += _correlate_by_ip(incidents)
    results += _correlate_escalation(incidents)

    # deduplicate by frozenset of incident IDs
    seen   = set()
    unique = []
    for r in results:
        key = frozenset(r["incident_ids"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    logger.info("Correlation complete | groups=%d", len(unique))
    return unique

# rules 
# Group incidents by username within the time frame
def _correlate_by_user(incidents: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for inc in incidents:
        user = inc["context"].get("username", "").strip()
        if not user or user == "unknown":
            continue
        groups.setdefault(user, []).append(inc)
        results = []
    for user, group in groups.items():
        if len(group) < MIN_INCIDENTS:
            continue
        results.append({
            "correlation_type": "same_user",
            "entity":           user,
            "entity_type":      "username",
            "incident_count":   len(group),
            "incident_ids":     [i["id"] for i in group],
            "max_score":        max(i["risk_score"] for i in group),
            "alert_levels":     [i["alert_level"] for i in group],
            "summary": (
                f"User '{user}' triggered {len(group)} incidents within "
                f"{WINDOW_MINUTES} minutes. Possible account compromise or "
                f"coordinated attack."
            ),
        })
    return results

# Group incidents by IP address within the time frame
def _correlate_by_ip(incidents: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for inc in incidents:
        ip = inc["context"].get("ip_address", "").strip()
        if not ip or ip == "unknown":
            continue
        groups.setdefault(ip, []).append(inc)

    results = []
    for ip, group in groups.items():
        if len(group) < MIN_INCIDENTS:
            continue

        # only flag if more than one unique user is involved
        users = set(i["context"].get("username", "") for i in group)

        results.append({
            "correlation_type": "same_ip",
            "entity":           ip,
            "entity_type":      "ip_address",
            "incident_count":   len(group),
            "incident_ids":     [i["id"] for i in group],
            "max_score":        max(i["risk_score"] for i in group),
            "alert_levels":     [i["alert_level"] for i in group],
            "affected_users":   list(users),
            "summary": (
                f"IP '{ip}' was involved in {len(group)} incidents within "
                f"{WINDOW_MINUTES} minutes across {len(users)} user(s). "
                f"Possible coordinated or automated attack."
            ),
        })
    return results

