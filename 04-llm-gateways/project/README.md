# Multi-Model Chatbot API

FastAPI chatbot that routes through a **LiteLLM gateway** using two **Groq** models - `qwen/qwen3.8-27b` (primary, bigger) and `openai/gpt-oss-20b` (fallback, smaller). Retries, timeout, fallback, and caching all happen in the LiteLLM `Router` in `main.py` - the API routes never know which model answered.

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
| `/chat/graph_route` | POST `{"message": "...", "simulate_primary_failure": false}` | Same fallback idea, built with a LangGraph routing graph instead of LiteLLM |

## What the gateway does (`main.py`)

- **Fallback** - if the primary (27b) model fails, automatically retries on the fallback (20b) model
- **Retries** - up to 2 attempts per model before falling back
- **Timeout** - 10s hard limit per request
- **Cooldown** - a failing model is skipped for 5s before being retried
- **Caching** - identical non-streaming prompts are served from cache, $0 cost

## Bonus: the same fallback, built with LangGraph (`/chat/graph_route`)

LiteLLM's `Router` handles fallback at the **infra layer** (a failed HTTP call triggers it).
`/chat/graph_route` shows the same decision at the **orchestration layer**, as an explicit graph:

```
primary node -> conditional edge (did it fail?) -> fallback node -> done
                          |
                          v (no failure)
                         done
```

Set `"simulate_primary_failure": true` to force the primary node to fail and watch the graph
route to the fallback model:

```bash
# normal - uses the primary model
curl -X POST http://localhost:8010/chat/graph_route \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Say hello in five words.\",\"simulate_primary_failure\":false}"

# forced failure - routes to the fallback model
curl -X POST http://localhost:8010/chat/graph_route \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Say hello in five words.\",\"simulate_primary_failure\":true}"
```

Use LiteLLM (or a similar library) for real infra-level routing in production. Use a graph like
this when the routing decision needs logic LiteLLM does not have out of the box - a content
check, a cost budget, or a step that depends on what an earlier node in your pipeline did.
