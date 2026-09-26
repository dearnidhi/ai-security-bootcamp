"""Guardrail primitives for the civic helpdesk graph."""

import re

PII_PATTERNS = {
    "phone": r"\b(\+91|0)?[6-9]\d{9}\b",
    "email": r"\b[\w.+-]+@[\w-]+\.\w{2,}\b",
    "aadhar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
}

INJECTION_PATTERNS = [
    r"ignore (previous|all|above) instructions",
    r"you are now",
    r"pretend (you are|to be)",
    r"forget (everything|your|all)",
    r"jailbreak",
]

BANNED_KEYWORDS = ["bomb", "hack", "kill", "exploit", "malware", "ransomware"]

CIVIC_TOPIC_KEYWORDS = [
    "water", "tanker", "supply", "pipeline", "garbage", "waste", "segregate",
    "collection", "property tax", "tax", "pid", "rebate", "penalty",
    "birth certificate", "death certificate", "certificate", "ward",
    "complaint", "municipal", "sewage", "drainage", "streetlight", "road",
]

SCAM_TRIGGER_PHRASES = [
    "otp", "one time password", "bank account number", "cvv", "atm pin",
    "upi pin", "aadhar number", "share your password", "account password",
]


class InputGuardrail:
    def __init__(self, max_length=1000, mask_pii=True):
        self.max_length = max_length
        self.mask_pii = mask_pii

    def run(self, text):
        result = {"safe_input": text, "blocked": False, "reason": None}

        if len(text.strip()) > self.max_length:
            result["blocked"] = True
            result["reason"] = f"Message too long (max {self.max_length} chars)."
            return result

        lower = text.lower()

        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, lower):
                result["blocked"] = True
                result["reason"] = "That doesn't look like a genuine question."
                return result

        bad = [w for w in BANNED_KEYWORDS if w in lower]
        if bad:
            result["blocked"] = True
            result["reason"] = "That message contains disallowed content."
            return result

        if self.mask_pii:
            masked = text
            for name, pattern in PII_PATTERNS.items():
                masked = re.sub(pattern, f"[{name.upper()}_REDACTED]", masked)
            result["safe_input"] = masked

        return result


class TopicGuardrail:
    def run(self, text):
        lower = text.lower()
        is_civic = any(kw in lower for kw in CIVIC_TOPIC_KEYWORDS)
        return {
            "blocked": not is_civic,
            "reason": None if is_civic else (
                "I only answer questions about municipal services: water, "
                "garbage, property tax, and certificates."
            ),
        }


class ScamGuardrail:
    """The single most important guardrail for a citizen-facing bot:
    never engage with requests that smell like an OTP/bank-detail scam,
    whether it's the user being tricked or trying to trick the bot."""

    def run(self, text):
        lower = text.lower()
        hits = [p for p in SCAM_TRIGGER_PHRASES if p in lower]
        return {
            "blocked": bool(hits),
            "reason": (
                "This office will never ask for or discuss OTPs, PINs, "
                "passwords, or bank account details over chat. Please "
                "visit your ward office in person for anything like that."
            ) if hits else None,
        }


class OutputGuardrail:
    def __init__(self, max_length=1500):
        self.max_length = max_length

    def run(self, response):
        result = {"final_response": response, "blocked": False, "reason": None}

        found = [pii for pii, pattern in PII_PATTERNS.items() if re.search(pattern, response)]
        if found:
            result.update({
                "blocked": True,
                "reason": f"Response withheld — it contained {found}.",
                "final_response": "Sorry, I can't share that. Please contact your ward office directly.",
            })
            return result

        if len(response) > self.max_length:
            result["final_response"] = response[: self.max_length] + "\n[Truncated]"

        return result
