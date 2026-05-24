"""
scripts/init_db.py
────────────────────────────────────────────────────────────
Sentinel – Database Initialiser

Creates the SQLite database and incidents table.
Safe to run multiple times — uses CREATE TABLE IF NOT EXISTS.

Usage:
    python scripts/init_db.py
"""

import sqlite3
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
DB_DIR  = ROOT / "db"
DB_PATH = DB_DIR / "incidents.db"


def init() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            risk_score   INTEGER NOT NULL,
            alert_level  TEXT    NOT NULL,
            reason_flags TEXT    NOT NULL DEFAULT '',
            event_type   TEXT    NOT NULL DEFAULT 'unknown',
            timestamp    TEXT    NOT NULL
        )
    """)
    con.commit()
    con.close()
    print(f"Database ready: {DB_PATH}")


if __name__ == "__main__":
    init()