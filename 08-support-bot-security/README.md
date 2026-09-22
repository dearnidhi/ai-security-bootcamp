# 08 — Live Demo (Capstone)

A support bot that ties everything together — guardrail + agent tool use + evaluator — all in one request.

## What it does

An order support bot with a `get_order_status` tool. An attack message asks for one legitimate order plus a range of other customers' orders.

1. **Guardrail** — detects bulk data requests, blocks in protected mode
2. **Agent** — calls `get_order_status` for each order it decides to look up
3. **Evaluator** — counts how many different customers' data appeared in one response

- **Vulnerable mode** — all data returned, no checks
- **Protected mode** — guardrail blocks the bulk request before the agent even runs

**Built with LangGraph** (via `langchain.agents.create_agent` + `langchain-groq`) for the agent
step. Model: `openai/gpt-oss-20b`.

## Run

```bash
# From inside this folder
..\venv\Scripts\activate
copy .env.example .env    # add GROQ_API_KEY

# Terminal 1
uvicorn main:app --reload --port 8003

# Terminal 2
streamlit run app.py
```

## Files

| File | What it does |
|------|-------------|
| `main.py` | FastAPI `/support_chat` — guardrail, LangGraph agent, evaluator |
| `app.py` | Streamlit UI — trace, response, evaluator verdict |
| `live_demo_explained.ipynb` | Full walkthrough of the demo |
