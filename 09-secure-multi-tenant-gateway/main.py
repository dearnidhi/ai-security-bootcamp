import os
import time
from collections import deque

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-20b"

app = FastAPI(title="Secure Multi-Tenant AI Gateway - IDOR/BOLA Case Study")

# --- Identity store (simulates an identity provider / API key vault) ---
API_KEYS = {
    "sk-legal-admin-001":    {"tenant": "legal",   "role": "admin"},
    "sk-legal-analyst-002":  {"tenant": "legal",   "role": "analyst"},
    "sk-finance-analyst-003": {"tenant": "finance", "role": "analyst"},
    "sk-finance-viewer-004": {"tenant": "finance", "role": "viewer"},
    "sk-hr-viewer-005":      {"tenant": "hr",       "role": "viewer"},
}

# --- Per-tenant confidential context (simulates a secrets manager) ---
TENANT_SECRETS = {
    "legal": "CONFIDENTIAL Case #4521: Acme Corp agreed to pay a $2,000,000 settlement. "
             "Do not disclose outside the Legal team.",
    "finance": "CONFIDENTIAL Q3 report: Revenue is $18M. A 30-person layoff is planned for "
               "December, not yet announced to staff.",
    "hr": "CONFIDENTIAL HR record: Employee ID 1042 salary is $145,000, currently on a "
          "performance improvement plan.",
}

ROLE_RATE_LIMITS = {"admin": 20, "analyst": 10, "viewer": 3}  # requests per 60 seconds
RATE_WINDOWS: dict[str, deque] = {}
AUDIT_LOG: list[dict] = []


def mask(key: str) -> str:
    return key[:10] + "..." if len(key) > 10 else key


def log_event(**kwargs):
    kwargs["time"] = time.strftime("%H:%M:%S")
    AUDIT_LOG.append(kwargs)
    if len(AUDIT_LOG) > 200:
        AUDIT_LOG.pop(0)


def rate_limited(api_key: str, role: str) -> bool:
    now = time.time()
    window = RATE_WINDOWS.setdefault(api_key, deque())
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= ROLE_RATE_LIMITS[role]:
        return True
    window.append(now)
    return False


def ask_groq(tenant: str, question: str) -> str:
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": (
                f"You are an internal assistant for the {tenant} department. "
                f"Use ONLY this confidential context to answer:\n\n{TENANT_SECRETS[tenant]}\n\n"
                f"Question: {question}"
            ),
        }],
        temperature=0,
        reasoning_effort="low",
        max_completion_tokens=512,
    )
    return completion.choices[0].message.content


class QueryRequest(BaseModel):
    api_key: str
    tenant_id: str
    question: str


@app.post("/vulnerable/query")
def vulnerable_query(req: QueryRequest):
    """BUG: only checks that the API key is valid - then trusts the client-supplied
    tenant_id to decide whose confidential data to use. This is a Broken Object-Level
    Authorization (BOLA/IDOR) flaw: identity is authenticated, but the requested
    OBJECT (tenant's data) is never checked against that identity."""
    identity = API_KEYS.get(req.api_key)
    if not identity:
        log_event(api_key=mask(req.api_key), tenant_claimed=req.tenant_id, mode="vulnerable",
                   allowed=False, reason="invalid api key")
        return {"error": "invalid api key"}

    if req.tenant_id not in TENANT_SECRETS:
        return {"error": "unknown tenant_id"}

    answer = ask_groq(req.tenant_id, req.question)
    log_event(api_key=mask(req.api_key), tenant_claimed=req.tenant_id, tenant_used=req.tenant_id,
               role=identity["role"], mode="vulnerable", allowed=True,
               reason="client-supplied tenant_id trusted without checking ownership")
    return {"tenant_used": req.tenant_id, "answer": answer}


@app.post("/secure/query")
def secure_query(req: QueryRequest):
    """FIX: tenant is derived ONLY from the authenticated api_key's own record.
    Any client-supplied tenant_id is treated as an untrusted claim - if it doesn't
    match, the request still succeeds using the REAL tenant, and the mismatch is
    logged as a possible attack attempt."""
    identity = API_KEYS.get(req.api_key)
    if not identity:
        log_event(api_key=mask(req.api_key), tenant_claimed=req.tenant_id, mode="secure",
                   allowed=False, reason="invalid api key")
        return {"error": "invalid api key"}

    real_tenant = identity["tenant"]
    role = identity["role"]
    cross_tenant_attempt = req.tenant_id != real_tenant

    if rate_limited(req.api_key, role):
        log_event(api_key=mask(req.api_key), tenant_claimed=req.tenant_id, tenant_used=real_tenant,
                   role=role, mode="secure", allowed=False, reason="rate limit exceeded")
        return {"error": f"rate limit exceeded for role '{role}'"}

    answer = ask_groq(real_tenant, req.question)
    log_event(api_key=mask(req.api_key), tenant_claimed=req.tenant_id, tenant_used=real_tenant,
               role=role, mode="secure", allowed=True,
               reason="cross-tenant attempt blocked, served real tenant only" if cross_tenant_attempt
               else "normal request")
    return {
        "tenant_used": real_tenant,
        "answer": answer,
        "cross_tenant_attempt_blocked": cross_tenant_attempt,
    }


@app.get("/secure/audit-log")
def audit_log(api_key: str):
    """Admin-only, and tenant-scoped: an admin only ever sees their OWN tenant's
    audit trail - tenant isolation applies to the audit log too."""
    identity = API_KEYS.get(api_key)
    if not identity or identity["role"] != "admin":
        log_event(api_key=mask(api_key), mode="secure", allowed=False,
                   reason="audit log access denied - admin role required")
        return {"error": "forbidden - admin role required"}

    tenant = identity["tenant"]
    scoped = [e for e in AUDIT_LOG if e.get("tenant_used") == tenant or e.get("tenant_claimed") == tenant]
    return {"tenant": tenant, "entries": scoped[-50:]}


@app.get("/identities")
def identities():
    return {k: v for k, v in API_KEYS.items()}


@app.get("/")
def root():
    return {"status": "ok"}
