"""
Guardrails - 4 safety checks for AI apps in one file.

1. InputGuardrail   - checks user input BEFORE the AI sees it
2. OutputGuardrail  - checks AI response BEFORE the user sees it
3. TopicalGuardrail - keeps the AI on-topic
4. AgenticGuardrail - controls which tools an AI agent can use
"""

import re
from enum import Enum


# ──────────────────────────────────────────────────────────────────────────────
# 1. INPUT GUARDRAIL
# ──────────────────────────────────────────────────────────────────────────────

PII_PATTERNS = {
    "phone":  r"\b(\+91|0)?[6-9]\d{9}\b",
    "email":  r"\b[\w.+-]+@[\w-]+\.\w{2,}\b",
    "aadhar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "pan":    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
}

INJECTION_PATTERNS = [
    r"ignore (previous|all|above) instructions",
    r"you are now",
    r"pretend (you are|to be)",
    r"forget (everything|your|all)",
    r"jailbreak",
]

BANNED_KEYWORDS = ["bomb", "hack", "kill", "exploit", "malware", "ransomware"]


class InputGuardrail:
    def __init__(self, max_length: int = 2000, mask_pii: bool = True):
        self.max_length = max_length
        self.mask_pii = mask_pii

    def run(self, text: str) -> dict:
        result = {"original_input": text, "safe_input": text, "blocked": False, "block_reason": None, "warnings": []}

        if len(text.strip()) > self.max_length:
            result["blocked"] = True
            result["block_reason"] = f"Input too long (max {self.max_length} chars)"
            return result

        for p in INJECTION_PATTERNS:
            if re.search(p, text.lower()):
                result["blocked"] = True
                result["block_reason"] = f"Prompt injection detected: '{p}'"
                return result

        bad = [kw for kw in BANNED_KEYWORDS if kw in text.lower()]
        if bad:
            result["blocked"] = True
            result["block_reason"] = f"Harmful keywords found: {bad}"
            return result

        if self.mask_pii:
            masked = text
            found = []
            for pii, pattern in PII_PATTERNS.items():
                if re.search(pattern, masked):
                    found.append(pii)
                    masked = re.sub(pattern, f"[{pii.upper()}_REDACTED]", masked)
            if found:
                result["warnings"].append(f"PII masked: {found}")
                result["safe_input"] = masked

        return result


# ──────────────────────────────────────────────────────────────────────────────
# 2. OUTPUT GUARDRAIL
# ──────────────────────────────────────────────────────────────────────────────

HARMFUL_OUTPUT_PATTERNS = [
    r"(steps? to make|how to (make|build)).{0,30}(bomb|weapon|malware)",
    r"(i (will|can) help you).{0,30}(hack|attack|exploit)",
]

SAFE_FALLBACK = "I'm sorry, I cannot provide a response to that request. Please rephrase or ask something else."


class OutputGuardrail:
    def __init__(self, max_length: int = 5000):
        self.max_length = max_length

    def run(self, response: str) -> dict:
        result = {"original_response": response, "final_response": response, "blocked": False, "block_reason": None, "warnings": []}

        for p in HARMFUL_OUTPUT_PATTERNS:
            if re.search(p, response.lower()):
                result.update({"blocked": True, "block_reason": f"Harmful content detected", "final_response": SAFE_FALLBACK})
                return result

        found = [pii for pii, pat in PII_PATTERNS.items() if re.search(pat, response)]
        if found:
            result.update({"blocked": True, "block_reason": f"PII in AI response: {found}", "final_response": SAFE_FALLBACK})
            return result

        if len(response) > self.max_length:
            result["warnings"].append(f"Response truncated to {self.max_length} chars")
            result["final_response"] = response[:self.max_length] + "\n[Truncated]"

        return result


# ──────────────────────────────────────────────────────────────────────────────
# 3. TOPICAL GUARDRAIL
# ──────────────────────────────────────────────────────────────────────────────

TOPICS = {
    "tech_support": ["error", "crash", "install", "update", "bug", "fix", "password", "login", "software", "hardware"],
    "finance":      ["loan", "bank", "credit", "debit", "payment", "tax", "invoice", "investment"],
    "general_ai":   ["machine learning", "ai", "neural network", "llm", "chatbot", "prompt", "dataset"],
    "off_topic":    ["recipe", "cook", "movie", "cricket", "joke", "travel", "celebrity", "football"],
}


class TopicalGuardrail:
    def __init__(self, allowed_topics: list[str]):
        self.allowed_topics = allowed_topics

    def run(self, text: str) -> dict:
        scores = {t: sum(1 for kw in kws if kw in text.lower()) for t, kws in TOPICS.items()}
        dominant = max(scores, key=scores.get) if max(scores.values()) > 0 else None
        result = {"user_input": text, "detected_topic": dominant or "unknown", "topic_scores": scores, "blocked": False, "block_reason": None}
        if dominant and dominant not in self.allowed_topics:
            result.update({"blocked": True, "block_reason": f"Topic '{dominant}' not in allowed: {self.allowed_topics}"})
        return result


# ──────────────────────────────────────────────────────────────────────────────
# 4. AGENTIC GUARDRAIL
# ──────────────────────────────────────────────────────────────────────────────

class RiskLevel(Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"

TOOL_REGISTRY = {
    "search_web": RiskLevel.LOW, "read_file": RiskLevel.LOW, "get_weather": RiskLevel.LOW,
    "write_file": RiskLevel.MEDIUM, "update_database": RiskLevel.MEDIUM, "create_calendar_event": RiskLevel.MEDIUM,
    "send_email": RiskLevel.HIGH, "delete_file": RiskLevel.HIGH,
    "make_payment": RiskLevel.HIGH, "execute_code": RiskLevel.HIGH, "call_external_api": RiskLevel.HIGH,
}

RISK_ORDER = {"low": 1, "medium": 2, "high": 3}


class AgenticGuardrail:
    def __init__(self, allowed_tools: list[str], max_risk_level: RiskLevel = RiskLevel.MEDIUM, require_human_approval_for_high: bool = True):
        self.allowed_tools = set(allowed_tools)
        self.max_risk_level = max_risk_level
        self.require_human_approval = require_human_approval_for_high
        self.action_log: list[dict] = []

    def check_action(self, tool_name: str, params: dict = None) -> dict:
        params = params or {}
        result = {"tool": tool_name, "params": params, "allowed": False, "reason": None, "requires_human_approval": False, "risk_level": None}

        if tool_name not in TOOL_REGISTRY:
            result["reason"] = f"Unknown tool '{tool_name}'"
        elif tool_name not in self.allowed_tools:
            result["reason"] = f"Tool '{tool_name}' not in agent's allowed list"
        elif RISK_ORDER[TOOL_REGISTRY[tool_name].value] > RISK_ORDER[self.max_risk_level.value]:
            result["reason"] = f"Tool risk '{TOOL_REGISTRY[tool_name].value}' exceeds max '{self.max_risk_level.value}'"
        else:
            result["risk_level"] = TOOL_REGISTRY[tool_name].value
            result["allowed"] = True
            if TOOL_REGISTRY[tool_name] == RiskLevel.HIGH and self.require_human_approval:
                result["requires_human_approval"] = True
                result["reason"] = "HIGH risk - requires human approval before execution"
            else:
                result["reason"] = "Action approved"

        self.action_log.append(result)
        return result

    def get_audit_log(self) -> list[dict]:
        return self.action_log


def simulate_human_approval(action: dict) -> bool:
    auto_approve = {"send_email", "create_calendar_event"}
    auto_deny = {"make_payment", "delete_file", "post_to_social"}
    tool = action["tool"]
    if tool in auto_approve:
        print(f"  [HUMAN] Auto-approving '{tool}'")
        return True
    if tool in auto_deny:
        print(f"  [HUMAN] Auto-denying '{tool}'")
        return False
    print(f"  [HUMAN] Default-approving '{tool}'")
    return True