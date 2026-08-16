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
