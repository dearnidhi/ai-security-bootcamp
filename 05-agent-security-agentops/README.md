# 05 — Agent Security

An AI customer support agent with real tools — shows what happens when an agent is tricked into misusing those tools.

## What it does

The agent has 2 tools: `lookup_invoice` and `send_email`.

A malicious support ticket asks the agent to email a customer's invoice (with card details) to an attacker's address.

- **Vulnerable mode** — agent sends the email to any address asked
- **Protected mode** — agent blocks sending to any address that doesn't match the verified customer email on file

The UI shows an "agent trace" — every tool call the agent made, what arguments it used, and what happened.

**Built with LangGraph** (via `langchain.agents.create_agent` + `langchain-groq`), not raw Groq
tool-calling — same ReAct-style loop, but expressed as a framework agent. Model: `openai/gpt-oss-20b`.

## Run

```bash
# From inside this folder
..\venv\Scripts\activate
copy .env.example .env    # add GROQ_API_KEY

# Terminal 1
uvicorn backend.main:app --reload --port 8001

# Terminal 2
streamlit run app.py
```

## Files

| File | What it does |
|------|-------------|
| `backend/main.py` | FastAPI `/handle_ticket` — tool definitions, agent loop, recipient guard |
| `app.py` | Streamlit UI — load legit/malicious ticket, switch mode, see trace |
| `agent_security_agentops_explained.ipynb` | Agent security concepts explained simply |
