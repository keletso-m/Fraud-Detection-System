"""
engine/risk_engine.py
────────────────────────────────────────────────────────────
Sentinel – Central Risk Engine

Combines activity and transaction scores into a single unified
risk result, assigns an alert level, and persists the incident
to SQLite.

Usage:
    result = evaluate(activity_result, transaction_result, context)
    result.risk_score    # int 0–100
    result.alert_level   # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    result.reason_flags  # list[str]
    result.to_dict()     # serialisable dict for API responses
"""

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("sentinel.risk_engine")

# ── DB path ────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "incidents.db"

# ── Blending weights ───────────────────────────────────────────────────────────
WEIGHT_ACTIVITY:     float = 0.5
WEIGHT_TRANSACTION:  float = 0.5

# ── Alert level thresholds ─────────────────────────────────────────────────────
LEVEL_CRITICAL: int = 75
LEVEL_HIGH:     int = 50
LEVEL_MEDIUM:   int = 25


# ── Result dataclass ───────────────────────────────────────────────────────────

@dataclass
class RiskResult:
    risk_score:   int
    alert_level:  str
    reason_flags: list[str]
    event_type:   str
    timestamp:    str
    incident_id:  int | None = None
    context:      dict       = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id":           self.incident_id,
            "risk_score":   self.risk_score,
            "alert_level":  self.alert_level,
            "reason_flags": self.reason_flags,
            "event_type":   self.event_type,
            "timestamp":    self.timestamp,
            "context":      self.context,
        }


# ── Public interface ───────────────────────────────────────────────────────────

def evaluate(
    activity_result:    dict,
    transaction_result: dict,
    context:            dict | None = None,
) -> RiskResult:
    """
    Combine activity + transaction scores into a unified RiskResult.
    Persists the incident to SQLite and returns the full result.
    """
    context = context or {}

    activity_score    = int(activity_result.get("activity_score", 0))
    transaction_score = int(transaction_result.get("transaction_score", 0))

    blended = int(
        activity_score    * WEIGHT_ACTIVITY +
        transaction_score * WEIGHT_TRANSACTION
    )
    final_score = _clamp(blended)
    alert_level = _assign_level(final_score)

    all_reasons = (
        activity_result.get("reasons", []) +
        transaction_result.get("reasons", [])
    )

    event_type = _infer_event_type(activity_score, transaction_score)
    timestamp  = datetime.now(timezone.utc).isoformat()

    result = RiskResult(
        risk_score   = final_score,
        alert_level  = alert_level,
        reason_flags = all_reasons,
        event_type   = event_type,
        timestamp    = timestamp,
        context      = context,
    )

    result.incident_id = _persist(result)

    logger.info(
        "Risk evaluation complete | score=%d level=%s event=%s reasons=%d",
        final_score, alert_level, event_type, len(all_reasons),
    )

    return result


# ── Private helpers ────────────────────────────────────────────────────────────

def _assign_level(score: int) -> str:
    if score >= LEVEL_CRITICAL:
        return "CRITICAL"
    if score >= LEVEL_HIGH:
        return "HIGH"
    if score >= LEVEL_MEDIUM:
        return "MEDIUM"
    return "LOW"


def _infer_event_type(activity_score: int, transaction_score: int) -> str:
    if activity_score > 0 and transaction_score > 0:
        return "combined"
    if transaction_score > 0:
        return "transaction"
    return "activity"


def _clamp(value: int) -> int:
    return min(max(value, 0), 100)


def _persist(result: RiskResult) -> int | None:
    """Write the incident to SQLite. Returns the new row ID, or None on failure."""
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("""
            INSERT INTO incidents
                (risk_score, alert_level, reason_flags, event_type, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            result.risk_score,
            result.alert_level,
            "|".join(result.reason_flags),
            result.event_type,
            result.timestamp,
        ))
        con.commit()
        row_id = cur.lastrowid
        con.close()
        return row_id
    except Exception as exc:
        logger.error("Failed to persist incident: %s", exc)
        return None