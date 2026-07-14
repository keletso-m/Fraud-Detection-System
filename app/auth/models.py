import sqlite3
from passlib.context import CryptContext

DB_PATH = "db/incidents.db"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") #hashing algorithm for passwords and adding salt to the password


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_user(username: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None


def create_user(username: str, password: str, role: str = "viewer") -> bool:
    """Returns False if username already exists, otherwise creates the user and returns True."""
    if get_user(username):
        return False
    hashed = hash_password(password)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
            (username, hashed, role),
        )
        conn.commit()
    return True