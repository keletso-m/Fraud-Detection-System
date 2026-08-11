_
EXPLANATIONS = {
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
