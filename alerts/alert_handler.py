"""
alerts/alert_handler.py
────────────────────────────────────────────────────────────
Sentinel – Alert Handler

Receives a RiskResult and dispatches it to:
  1. Colour-coded console output
  2. NDJSON rotating log file (logs/sentinel.log)

Usage:
    from alerts.alert_handler import dispatch
    dispatch(risk_result)
"""

import json
import logging
import logging.handlers
from pathlib import Path

logger = logging.getLogger("sentinel.alert_handler")

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent.parent
LOG_DIR  = ROOT / "logs"
LOG_FILE = LOG_DIR / "sentinel.log"

# ── ANSI colour codes ──────────────────────────────────────────────────────────
COLOURS = {
    "LOW":      "\033[92m",   # green
    "MEDIUM":   "\033[93m",   # yellow
    "HIGH":     "\033[33m",   # orange (bold yellow)
    "CRITICAL": "\033[91m",   # red
}
RESET  = "\033[0m"
BOLD   = "\033[1m"

ICONS = {
    "LOW":      "🟢",
    "MEDIUM":   "🟡",
    "HIGH":     "🟠",
    "CRITICAL": "🔴",
}


# ── Public interface ───────────────────────────────────────────────────────────

def dispatch(result) -> None:
    """
    Dispatch a RiskResult to console and log file.
    Accepts either a RiskResult dataclass or a plain dict.
    """
    if hasattr(result, "to_dict"):
        data = result.to_dict()
    else:
        data = dict(result)

    _console(data)
    _log_ndjson(data)


# ── Private helpers ────────────────────────────────────────────────────────────

def _console(data: dict) -> None:
    level  = data.get("alert_level", "LOW")
    score  = data.get("risk_score", 0)
    icon   = ICONS.get(level, "⚪")
    colour = COLOURS.get(level, "")
    flags  = data.get("reason_flags", [])

    print(f"\n{colour}{BOLD}{'─' * 56}{RESET}")
    print(f"{icon}  {colour}{BOLD}SENTINEL ALERT — {level}{RESET}  (score: {score}/100)")
    print(f"   Event : {data.get('event_type', 'unknown')}")
    print(f"   Time  : {data.get('timestamp', '')}")
    if flags:
        print(f"   Flags :")
        for f in flags:
            print(f"     • {f}")
    else:
        print(f"   Flags : none")
    print(f"{colour}{BOLD}{'─' * 56}{RESET}\n")


def _log_ndjson(data: dict) -> None:
    """Append one NDJSON line to the rotating sentinel.log file."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(data) + "\n")
    except Exception as exc:
        logger.error("Failed to write alert log: %s", exc)