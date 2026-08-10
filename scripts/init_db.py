import sqlite3
import os

DB_PATH = "db/incidents.db"


def init():
    os.makedirs("db", exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL,
                event_type  TEXT    NOT NULL,
                risk_score  REAL    NOT NULL,
                severity    TEXT    NOT NULL,
                reasons     TEXT    NOT NULL,
                raw_event   TEXT    NOT NULL,
                 state       TEXT    NOT NULL DEFAULT 'open'
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                username        TEXT    NOT NULL UNIQUE,
                hashed_password TEXT    NOT NULL,
                role            TEXT    NOT NULL DEFAULT 'viewer'
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS incident_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id INTEGER NOT NULL,
                changed_by  TEXT    NOT NULL,
                field       TEXT    NOT NULL,
                old_value   TEXT    NOT NULL,
                new_value   TEXT    NOT NULL,
                timestamp   TEXT    NOT NULL,
                FOREIGN KEY (incident_id) REFERENCES incidents(id)
            )
        """)
        #  state column to existing incidents if or when upgrading
        try:
            conn.execute("ALTER TABLE incidents ADD COLUMN state TEXT NOT NULL DEFAULT 'open'")
        except sqlite3.OperationalError:
            pass
        # Add context column to existing incidents if upgrading 
        try:
            conn.execute("ALTER TABLE incidents ADD COLUMN context TEXT NOT NULL DEFAULT '{}'")
        except sqlite3.OperationalError:
            pass


        conn.commit()
    print(" Database initialised: incidents + users tables ready.")


if __name__ == "__main__":
    init()
    print("   Run 'python scripts/create_admin.py' to create your first admin user.")