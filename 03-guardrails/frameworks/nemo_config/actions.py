import re
from typing import Optional

from nemoguardrails.actions import action

INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior|above) instructions",
    r"reveal (your )?(system )?prompt",
]


@action(is_system_action=True)
async def check_prompt_injection(context: Optional[dict] = None):
    """Input rail: True if the user message looks like a prompt injection."""
    text = (context or {}).get("user_message", "")
    return any(re.search(p, text, re.I) for p in INJECTION_PATTERNS)


@action(is_system_action=True)
async def redact_secret(text: str):
    """Output rail: hide the internal discount code if the model says it."""
    return re.sub(r"SAVE-\d+|7391", "[REDACTED]", text, flags=re.I)
