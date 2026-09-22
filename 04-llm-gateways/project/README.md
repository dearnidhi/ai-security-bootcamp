# Multi-Model Chatbot API

FastAPI chatbot that routes through a **LiteLLM gateway** using two **Groq** models — `qwen/qwen3.8-27b` (primary, bigger) and `openai/gpt-oss-20b` (fallback, smaller). Retries, timeout, fallback, and caching all happen in the LiteLLM `Router` in `main.py` — the API routes never know which model answered.

## Setup

```bash
pip install -r requirements.txt
```

Add your free Groq key to the shared `.env` in the project root (or to `04-llm-gateways/.env`):

```
GROQ_API_KEY=gsk_...
```

Get a free key: https://console.groq.com/keys

## Run

```bash
uvicorn main:app --reload
```

## Endpoints

| Endpoint | Method | What it does |
| --- | --- | --- |
| `/health` | GET | Liveness check |
| `/chat` | POST `{"message": "..."}` | Returns reply, model actually used, and estimated cost (`null` if LiteLLM has no price for that model) |
| `/chat/stream` | POST `{"message": "..."}` | Streams the reply token-by-token |

## What the gateway does (`main.py`)

- **Fallback** — if the primary (27b) model fails, automatically retries on the fallback (20b) model
- **Retries** — up to 2 attempts per model before falling back
- **Timeout** — 10s hard limit per request
- **Cooldown** — a failing model is skipped for 5s before being retried
- **Caching** — identical non-streaming prompts are served from cache, $0 cost
