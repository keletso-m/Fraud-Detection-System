
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("sentinel.risk_engine")

#  DB path 
ROOT    = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "incidents.db"

#  Blending weights 
WEIGHT_ACTIVITY:    float = 0.5
WEIGHT_TRANSACTION: float = 0.5

#  alert level thresholds 
LEVEL_CRITICAL: int = 75
LEVEL_HIGH:     int = 50
LEVEL_MEDIUM:   int = 25


#  Result dataclass 

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


#  Public interface

def evaluate(
    activity_result:    dict,
    transaction_result: dict,
    context:            dict | None = None,
) -> RiskResult:
     
    context = context or {}

    activity_score    = int(activity_result.get("activity_score", 0))
    transaction_score = int(transaction_result.get("transaction_score", 0))

    blended     = int(activity_score * WEIGHT_ACTIVITY + transaction_score * WEIGHT_TRANSACTION)
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


def get_incidents(limit: int = 50, min_score: int = 0) -> list[dict]:
    """Return recent incidents from the DB, newest first."""
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""
            SELECT id, risk_score, alert_level, reason_flags, event_type, timestamp
            FROM incidents
            WHERE risk_score >= ?
            ORDER BY id DESC
            LIMIT ?
        """, (min_score, limit))
        rows = cur.fetchall()
        con.close()
        return [_row_to_dict(row) for row in rows]
    except Exception as exc:
        logger.error("Failed to fetch incidents: %s", exc)
        return []


def get_incident_by_id(incident_id) -> dict | None:
    """Return a single incident by ID, or None if not found."""
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""
            SELECT id, risk_score, alert_level, reason_flags, event_type, timestamp
            FROM incidents
            WHERE id = ?
        """, (int(incident_id),))
        row = cur.fetchone()
        con.close()
        return _row_to_dict(row) if row else None
    except Exception as exc:
        logger.error("Failed to fetch incident %s: %s", incident_id, exc)
        return None

# incident states and severity workflow
VALID_STATES     = {"open", "investigating", "resolved", "false_positive"}
VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
# update incident state and record in history returns salse if not found
def update_incident_state(incident_id: int, new_state: str, changed_by: str) -> bool:
    if new_state not in VALID_STATES:
        raise ValueError(f"Invalid state '{new_state}'. Must be one of {VALID_STATES}")
    return _update_incident_field(incident_id, "state", new_state, changed_by)

# update incident severity returns false if not found
def update_incident_severity(incident_id: int, new_severity: str, changed_by: str) -> bool:
    if new_severity not in VALID_SEVERITIES:
        raise ValueError(f"Invalid severity '{new_severity}'. Must be one of {VALID_SEVERITIES}")
    return _update_incident_field(incident_id, "alert_level", new_severity, changed_by)

def get_incident_history(incident_id: int) -> list[dict]:
    """returns the full audit trail for an incident thenewest first."""
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""
            SELECT id, incident_id, changed_by, field, old_value, new_value, timestamp
            FROM incident_history
            WHERE incident_id = ?
            ORDER BY id DESC
        """, (incident_id,))
        rows = cur.fetchall()
        con.close()
        return [dict(row) for row in rows]
    except Exception as exc:
        logger.error("Failed to fetch history for incident %s: %s", incident_id, exc)
        return []

    def _update_incident_field(
    incident_id: int, field: str, new_value: str, changed_by: str
) -> bool:
    """Generic field updater, reads old value, writes new, logs history"""
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row

        # get current value
        row = con.execute(
            f"SELECT {field} FROM incidents WHERE id = ?", (incident_id,)
        ).fetchone()

        if not row:
            con.close()
            return False

        old_value = row[field]

        # update the incident
        con.execute(
            f"UPDATE incidents SET {field} = ? WHERE id = ?",
            (new_value, incident_id),
        )

        # write history record
        con.execute("""
            INSERT INTO incident_history
                (incident_id, changed_by, field, old_value, new_value, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            incident_id,
            changed_by,
            field,
            old_value,
            new_value,
            datetime.now(timezone.utc).isoformat(),
        ))

        con.commit()
        con.close()
        return True

    except Exception as exc:
        logger.error("Failed to update %s on incident %s: %s", field, incident_id, exc)
        return False

    
#helper functions 

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


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id":           row["id"],
        "risk_score":   row["risk_score"],
        "alert_level":  row["alert_level"],
        "reason_flags": row["reason_flags"].split("|") if row["reason_flags"] else [],
        "event_type":   row["event_type"],
        "timestamp":    row["timestamp"],
    }


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