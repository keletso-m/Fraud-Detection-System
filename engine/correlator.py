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

#Detect escalating severity for the same user within the time window."
def _correlate_escalation(incidents: list[dict]) -> list[dict]:
    """Detect escalating severity for the same user within the time window."""
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

        # sort by timestamp
        sorted_group = sorted(group, key=lambda i: i["timestamp"])
        levels = [SEVERITY_ORDER.get(i["alert_level"], 0) for i in sorted_group]

        # check if severity is strictly increasing
        is_escalating = all(levels[i] <= levels[i + 1] for i in range(len(levels) - 1))
        has_increase  = levels[-1] > levels[0]

        if is_escalating and has_increase:
            first = sorted_group[0]["alert_level"]
            last  = sorted_group[-1]["alert_level"]
            results.append({
                "correlation_type": "escalating_severity",
                "entity":           user,
                "entity_type":      "username",
                "incident_count":   len(sorted_group),
                "incident_ids":     [i["id"] for i in sorted_group],
                "max_score":        max(i["risk_score"] for i in sorted_group),
                "alert_levels":     [i["alert_level"] for i in sorted_group],
                "summary": (
                    f"User '{user}' shows escalating severity from {first} to {last} "
                    f"across {len(sorted_group)} incidents within {WINDOW_MINUTES} minutes. "
                    f"This is a strong indicator of an active attack in progress."
                ),
            })
    return results

# database fetch 
# fetch incidents from th last (WINDOW_MINUTES) minutes
def _fetch_recent() -> list[dict]:
    """Fetch incidents from the last WINDOW_MINUTES minutes."""
    try:
        cutoff = (
            datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)
        ).isoformat()

        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""
            SELECT id, risk_score, alert_level, event_type, timestamp, context
            FROM incidents
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """, (cutoff,))
        rows = cur.fetchall()
        con.close()

        result = []
        for row in rows:
            try:
                ctx = json.loads(row["context"]) if row["context"] else {}
            except Exception:
                ctx = {}
            result.append({
                "id":          row["id"],
                "risk_score":  row["risk_score"],
                "alert_level": row["alert_level"],
                "event_type":  row["event_type"],
                "timestamp":   row["timestamp"],
                "context":     ctx,
            })
        return result

    except Exception as exc:
        logger.error("Failed to fetch recent incidents for correlation: %s", exc)
        return []
    