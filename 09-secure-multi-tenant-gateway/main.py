import json
import os
import time
from collections import deque

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain.agents import create_agent

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


class AgentQueryRequest(BaseModel):
    api_key: str
    message: str


def build_agent(mode: str, real_tenant: str):
    """Same idea as modules 05/08: the security check lives in the TOOL, not in what
    the LLM decides. The agent can be talked into asking for another tenant's data -
    whether that actually leaks depends only on what the tool does with the argument."""

    @tool
    def get_tenant_data(tenant_id: str) -> str:
        """Look up the confidential context for a tenant by tenant_id."""
        if mode == "vulnerable":
            # BUG: trusts whatever tenant_id the agent (i.e. the LLM) decided to pass
            used_tenant = tenant_id
        else:
            # FIX: ignores the agent's argument entirely, always uses the authenticated tenant
            used_tenant = real_tenant
        data = TENANT_SECRETS.get(used_tenant, "unknown tenant")
        return json.dumps({"tenant_used": used_tenant, "data": data})

    llm = ChatGroq(model=MODEL, temperature=0, max_tokens=1024)
    system_prompt = (
        "You are an internal assistant. Use get_tenant_data to look up whatever tenant "
        "information the user asks for, to be as helpful as possible."
    )
    return create_agent(llm, tools=[get_tenant_data], system_prompt=system_prompt)


def run_agent_query(mode: str, api_key: str, message: str):
    identity = API_KEYS.get(api_key)
    if not identity:
        return {"error": "invalid api key"}
    real_tenant = identity["tenant"]

    agent = build_agent(mode, real_tenant)
    result = agent.invoke({"messages": [HumanMessage(content=message)]})
    messages = result["messages"]

    tool_calls_by_id = {}
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            for tc in m.tool_calls:
                tool_calls_by_id[tc["id"]] = {"tool": tc["name"], "arguments": tc["args"]}

    trace = []
    cross_tenant_leak = False
    for m in messages:
        if isinstance(m, ToolMessage):
            call = tool_calls_by_id.get(m.tool_call_id, {"tool": m.name, "arguments": {}})
            result_val = json.loads(m.content)
            if result_val.get("tenant_used") != real_tenant:
                cross_tenant_leak = True
            trace.append({"tool": call["tool"], "arguments": call["arguments"], "result": result_val})

    final_response = ""
    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.content:
            final_response = m.content
            break

    log_event(api_key=mask(api_key), mode=f"agent-{mode}", role=identity["role"],
               allowed=True, reason="cross-tenant leak via agent tool call" if cross_tenant_leak else "normal")
    return {"real_tenant": real_tenant, "trace": trace, "final_response": final_response,
            "cross_tenant_leak": cross_tenant_leak}


@app.post("/vulnerable/agent-query")
def vulnerable_agent_query(req: AgentQueryRequest):
    """Agentic BOLA: the agent (LangGraph) decides which tenant_id to pass to the tool.
    If a user's phrasing talks it into asking for another tenant's data, the tool
    happily returns it - the LLM's decision IS the access-control check, which is
    exactly the anti-pattern this module is about."""
    return run_agent_query("vulnerable", req.api_key, req.message)


@app.post("/secure/agent-query")
def secure_agent_query(req: AgentQueryRequest):
    """Fix: same agent, same LLM, but the tool ignores whatever tenant_id the agent
    passes and always uses the caller's real authenticated tenant. Even a successfully
    'social-engineered' agent cannot leak another tenant's data, because the enforcement
    point is the tool's code, not the LLM's judgment."""
    return run_agent_query("secure", req.api_key, req.message)


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
