

import logging

logger = logging.getLogger("sentinel.transaction_scorer")

#  Configurable thresholds 
HIGH_AMOUNT_THRESHOLD: float = 10_000.00   
RAPID_TX_COUNT_THRESHOLD: int = 3          # flag if >= this many in 60 seconds

#  Score weights 
WEIGHT_HIGH_AMOUNT:      int = 25
WEIGHT_RAPID_TX:         int = 30
WEIGHT_LOCATION_MISMATCH: int = 25
WEIGHT_NEW_DEVICE:       int = 20


#  Public interface 

def score(event: dict) -> dict:
    """
    Score one transaction event for fraud risk.

    Returns:
        {
            "transaction_score": int,         # 0–100
            "reasons":           list[str],   # human-readable flags
        }
    """
    points = 0
    reasons: list[str] = []

    # . High-value amount 
    amount = float(event.get("amount", 0))
    if amount > HIGH_AMOUNT_THRESHOLD:
        points += WEIGHT_HIGH_AMOUNT
        currency = event.get("currency", "")
        reasons.append(
            f"High-value transaction: {currency} {amount:,.2f} "
            f"(threshold: {currency} {HIGH_AMOUNT_THRESHOLD:,.2f})"
        )
        logger.debug("Flag: high amount (%.2f)", amount)

    #  Rapid repeated transactions 
    recent_count = int(event.get("recent_tx_count", 0))
    if recent_count >= RAPID_TX_COUNT_THRESHOLD:
        points += WEIGHT_RAPID_TX
        reasons.append(
            f"Rapid transactions: {recent_count} in the last 60 seconds "
            f"(threshold: {RAPID_TX_COUNT_THRESHOLD})"
        )
        logger.debug("Flag: rapid tx count (%d)", recent_count)

    #  Location mismatch 
    location      = str(event.get("location", "")).strip().lower()
    last_location = str(event.get("last_location", "")).strip().lower()
    if location and last_location and location != last_location:
        points += WEIGHT_LOCATION_MISMATCH
        reasons.append(
            f"Location mismatch: current '{event.get('location')}' vs "
            f"previous '{event.get('last_location')}'"
        )
        logger.debug("Flag: location mismatch (%s vs %s)", location, last_location)

    #  New / unrecognised device 
    device_id     = str(event.get("device_id", "")).strip()
    known_devices = [str(d).strip() for d in event.get("known_devices", [])]
    if device_id and device_id not in known_devices:
        points += WEIGHT_NEW_DEVICE
        reasons.append(f"Unrecognised device: {device_id}")
        logger.debug("Flag: new device (%s)", device_id)

    final_score = _clamp(points)

    logger.info(
        "Transaction analysis complete | account=%s amount=%.2f score=%d reasons=%d",
        event.get("account_id", "unknown"),
        amount,
        final_score,
        len(reasons),
    )

    return {
        "transaction_score": final_score,
        "reasons": reasons,
    }


# helper functions

def _clamp(score: int) -> int:
    """Clamp score to [0, 100]. Always call this before returning."""
    return min(max(score, 0), 100)