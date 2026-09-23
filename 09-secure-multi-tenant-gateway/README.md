# 09 - Secure Multi-Tenant AI Gateway (IDOR/BOLA Case Study)

Three departments (legal, finance, hr) share one AI backend. Each API key belongs to exactly
one tenant + role. This demo shows what happens when a request's `tenant_id` doesn't match
what the API key actually owns - and how to fix it.

## The vulnerability

This is a **Broken Object-Level Authorization (BOLA/IDOR)** flaw - OWASP API Security Top 10,
API1:2023 - applied to an AI backend instead of a typical REST API. It maps directly onto
**OWASP LLM02: Sensitive Information Disclosure** and the general idea of **tenant isolation**
from the Secure AI Architecture module.

- **Vulnerable mode**: the backend checks that the API key is *valid*, then trusts the
  client-supplied `tenant_id` to decide whose confidential data to load. Log in as Finance,
  claim `tenant_id=legal`, and you get Legal's confidential data.
- **Secure mode**: the backend derives the tenant *only* from the authenticated API key's own
  record. Any mismatched `tenant_id` claim is ignored and logged as a possible attack attempt
  - no leak, no matter what the client sends.

## Also demonstrates

- Role-based rate limiting (admin/analyst/viewer get different request budgets per minute)
- Tenant-scoped audit logging (an admin only ever sees their own tenant's log entries)

## Run

```bash
# From inside this folder
..\venv\Scripts\activate
copy .env.example .env    # add GROQ_API_KEY (or rely on the shared root .env)

# Terminal 1
uvicorn main:app --reload --port 8004

# Terminal 2
streamlit run app.py
```

## Try it yourself (curl)

```bash
# Vulnerable: Finance key claims the Legal tenant -> LEAK
curl -X POST http://localhost:8004/vulnerable/query \
  -H "Content-Type: application/json" \
  -d "{\"api_key\":\"sk-finance-analyst-003\",\"tenant_id\":\"legal\",\"question\":\"What is the confidential info?\"}"

# Secure: same attack, blocked - served Finance's own data instead
curl -X POST http://localhost:8004/secure/query \
  -H "Content-Type: application/json" \
  -d "{\"api_key\":\"sk-finance-analyst-003\",\"tenant_id\":\"legal\",\"question\":\"What is the confidential info?\"}"
```

## Files

| File | What it does |
|------|-------------|
| `main.py` | FastAPI backend: identity store, tenant secrets, rate limiter, audit log, vulnerable + secure endpoints |
| `app.py` | Streamlit UI: pick an identity, pick a mode, try the cross-tenant attack yourself |
