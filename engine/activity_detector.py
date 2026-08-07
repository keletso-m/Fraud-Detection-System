
import logging
from datetime import datetime, timezone

logger = logging.getLogger("sentinel.activity_detector")

# configurable thresholds 
FAILED_LOGIN_THRESHOLD: int = 5          
OFF_HOURS_START: int        = 0          
OFF_HOURS_END: int          = 5         

#  Known safe IP prefixes 
KNOWN_IP_PREFIXES: list[str] = [
    "10.",
    "192.168.",
    "172.16.",
    "127.",
]

#  Suspicious command fragments 
SUSPICIOUS_COMMANDS: list[str] = [
    "wget", "curl", "nc ", "netcat", "chmod +x",
    "/etc/passwd", "/etc/shadow", "base64", "python -c",
    "bash -i", "sh -i", "nmap", "masscan", "sqlmap",
]

#  Score weights 
WEIGHT_FAILED_LOGINS:   int = 30
WEIGHT_OFF_HOURS:       int = 15
WEIGHT_UNKNOWN_IP:      int = 25
WEIGHT_SUSPICIOUS_CMD:  int = 30


#  Public interface 

def analyse(event: dict) -> dict:
    
    #analyse one system activity event for intrusion signals 

    points  = 0
    reasons: list[str] = []

    # too many failed logins 
    failed = int(event.get("failed_logins", 0))
    if failed > FAILED_LOGIN_THRESHOLD:
        points += WEIGHT_FAILED_LOGINS
        reasons.append(
            f"Excessive failed logins: {failed} attempts "
            f"(threshold: {FAILED_LOGIN_THRESHOLD})"
        )
        logger.debug("Flag: failed logins (%d)", failed)

    #  weird hour access/ off hours 
    hour = _parse_hour(event.get("timestamp", ""))
    if hour is not None and OFF_HOURS_START <= hour <= OFF_HOURS_END:
        points += WEIGHT_OFF_HOURS
        reasons.append(
            f"Off-hours access: activity at {hour:02d}:00 UTC "
            f"(window: {OFF_HOURS_START:02d}:00–{OFF_HOURS_END:02d}:00 UTC)"
        )
        logger.debug("Flag: off-hours access (hour=%d)", hour)

    # unknown IP addresses
    ip = str(event.get("ip_address", "")).strip()
    if ip and not _is_known_ip(ip):
        points += WEIGHT_UNKNOWN_IP
        reasons.append(f"Unknown IP address: {ip}")
        logger.debug("Flag: unknown IP (%s)", ip)

    # suspicious command 
    command = str(event.get("command", "")).strip().lower()
    matched = _match_suspicious_command(command)
    if matched:
        points += WEIGHT_SUSPICIOUS_CMD
        reasons.append(f"Suspicious command detected: '{matched}'")
        logger.debug("Flag: suspicious command (%s)", matched)

    final_score = _clamp(points)

    logger.info(
        "Activity analysis complete | user=%s ip=%s score=%d reasons=%d",
        event.get("username", "unknown"),
        ip,
        final_score,
        len(reasons),
    )

    return {
        "activity_score": final_score,
        "reasons": reasons,
    }


#   helpers 

def _parse_hour(timestamp: str) -> int | None:
    """Extract UTC hour from an ISO-8601 timestamp string. Returns None on failure."""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).hour
    except (ValueError, AttributeError):
        return None


def _is_known_ip(ip: str) -> bool:
    """Return True if the IP starts with a known safe prefix."""
    return any(ip.startswith(prefix) for prefix in KNOWN_IP_PREFIXES)


def _match_suspicious_command(command: str) -> str | None:
    """Return the first suspicious fragment found in the command, or None."""
    for fragment in SUSPICIOUS_COMMANDS:
        if fragment in command:
            return fragment
    return None


def _clamp(value: int) -> int:
    """Clamp score to [0, 100]. Always call this before returning."""
    return min(max(value, 0), 100)