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