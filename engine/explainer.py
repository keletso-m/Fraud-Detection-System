_EXPLANATIONS = {
    "failed_logins > 5": (
        "Multiple failed login attempts were detected, exceeding the threshold of 5. "
        "This is a strong indicator of a brute force or credential stuffing attack."
    ),
    "off-hours access": (
        "System access was detected between 00:00 and 05:00 UTC. "
        "Activity during this window is unusual and warrants investigation."
    ),
    "unknown IP": (
        "The request originated from an IP address not in the known allowlist. "
        "This could indicate access from an unrecognised or compromised device."
    ),
    "suspicious command": (
        "A potentially dangerous system command was detected, such as attempts to read "
        "sensitive files or escalate privileges. Immediate review is recommended."
    ),
    "high amount": (
        "The transaction amount exceeds ZAR 10,000, which is above the normal threshold. "
        "Large transactions carry a higher risk of fraud."
    ),
    "rapid transactions": (
        "3 or more transactions were submitted within a 60-second window. "
        "This pattern is consistent with automated fraud or account takeover activity."
    ),
    "location mismatch": (
        "The transaction location does not match the user's previous known location. "
        "This could indicate that the account is being accessed from an unexpected region."
    ),
    "unknown device": (
        "The transaction was submitted from an unrecognised device not associated with "
        "this account. This is a common indicator of account compromise."
    ),
}

_FALLBACK = (
    "An anomalous signal was detected. Manual review of this incident is recommended."
)
# severity rationale
#return a readable explanation for each reason flag
def explain_flags(reason_flags: list[str]) -> list[str]:
    explanations = []
    for flag in reason_flags:
        # normalise flag to lowercase for matching
        matched = _EXPLANATIONS.get(flag.lower().strip())
        explanations.append(matched if matched else f"{flag}: {_FALLBACK}")
    return explanations
def explain_severity(
    score: int,
    alert_level: str,
    event_type: str,
    activity_score: int,
    transaction_score: int,
) -> str:
    """Generate a  readable and plain-English rationale for the overall risk score"""
    parts = []

    if event_type == "combined":
        parts.append(
            f"Both activity and transaction detectors fired simultaneously. "
            f"Activity score: {activity_score}/100, transaction score: {transaction_score}/100. "
            f"Combined signals produce a significantly elevated risk."
        )
    elif event_type == "transaction":
        parts.append(
            f"This incident was driven entirely by transaction signals "
            f"with a raw score of {transaction_score}/100."
        )
    else:
        parts.append(
            f"This incident was driven entirely by activity signals "
            f"with a raw score of {activity_score}/100."
        )

    level_map = {
        "CRITICAL": "The final blended score of {score}/100 exceeds the CRITICAL threshold (75+). Immediate action is strongly recommended.",
        "HIGH":     "The final blended score of {score}/100 exceeds the HIGH threshold (50+). This incident should be investigated promptly.",
        "MEDIUM":   "The final blended score of {score}/100 exceeds the MEDIUM threshold (25+). This incident warrants monitoring and review.",
        "LOW":      "The final blended score of {score}/100 is below the MEDIUM threshold. This incident is low risk but has been logged for visibility.",
    }

    parts.append(level_map[alert_level].format(score=score))

    return " ".join(parts)

