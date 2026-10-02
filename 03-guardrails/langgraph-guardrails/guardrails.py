"""Guardrail checks. Each check returns a refusal message if it blocks, else None."""

import re

PII_PATTERNS = {
    "phone": r"\b(\+91|0)?[6-9]\d{9}\b",
    "email": r"\b[\w.+-]+@[\w-]+\.\w{2,}\b",
    "aadhar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
}

INJECTION_PATTERN = r"ignore (all |previous |above )+instructions|you are now|pretend (you are|to be)|jailbreak"
SCAM_PATTERN = r"\b(otp|cvv|upi pin|atm pin|password|bank account number)\b"

CIVIC_KEYWORDS = [
    "water", "tanker", "pipeline", "supply", "bill", "refund",
    "property", "tax", "pid", "rebate", "penalty", "ward", "municipal", "complaint",
]


def mask_pii(text):
    for name, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"[{name.upper()}]", text)
    return text


def check_injection(text):
    if re.search(INJECTION_PATTERN, text.lower()):
        return "I can't process that. It doesn't look like a genuine question."


def check_scam(text):
    if re.search(SCAM_PATTERN, text.lower()):
        return ("This office will never ask for OTPs, PINs, passwords or bank details. "
                "Please visit your ward office in person.")


def check_topic(text):
    if not any(kw in text.lower() for kw in CIVIC_KEYWORDS):
        return "I only answer questions about water supply and property tax."


def check_output(text):
    if any(re.search(pattern, text) for pattern in PII_PATTERNS.values()):
        return "Sorry, I can't share that. Please contact your ward office directly."
