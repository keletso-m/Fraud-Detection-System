def explain_flags(reason_flags: list[str]) -> list[str]:
    """Return a readable or undastandable  explanation for each reason flag."""
    explanations = []
    for flag in reason_flags:
        explanation = _match_flag(flag)
        explanations.append(explanation)
    return explanations

def _match_flag(flag: str) -> str:
    f = flag.lower()
    if "failed login" in f:
        return (
            "Multiple failed login attempts were detected, exceeding the threshold of 5. "
            "This is a strong indicator of a brute force or credential stuffing attack."
        )
    if "off-hours" in f:
        return (
            "System access was detected between 00:00 and 05:00 UTC. "
            "Activity during this window is unusual and warrants investigation."
        )
    if "unknown ip" in f:
        return (
            "The request originated from an IP address not in the known allowlist. "
            "This could indicate access from an unrecognised or compromised device."
        )
    if "suspicious command" in f:
        return (
            "A potentially dangerous system command was detected, such as attempts to read "
            "sensitive files or escalate privileges. Immediate review is recommended."
        )
    if "high amount" in f or "amount" in f:
        return (
            "The transaction amount exceeds ZAR 10,000, which is above the normal threshold. "
            "Large transactions carry a higher risk of fraud."
        )
    if "rapid transaction" in f:
        return (
            "3 or more transactions were submitted within a 60-second window. "
            "This pattern is consistent with automated fraud or account takeover activity."
        )
    if "location mismatch" in f:
        return (
            "The transaction location does not match the user's previous known location. "
            "This could indicate that the account is being accessed from an unexpected region."
        )
    if "unknown device" in f:
        return (
            "The transaction was submitted from an unrecognised device not associated with "
            "this account. This is a common indicator of account compromise."
        )
    return f"{flag}: An anomalous signal was detected. Manual review of this incident is recommended."

