# 04 - LLM Gateways

A gateway is a layer between your app and the LLM provider that adds retries, fallback, caching, and cost tracking - without changing your business logic.

## What's covered

| Concept | What it solves |
|---------|---------------|
| `completion(model="groq/model")` | One interface for any provider |
| `num_retries` | Auto-retry on rate limits or errors |
| `timeout` | Don't let a stuck request block your app |
| `Router` + `fallbacks` | Primary model fails → backup takes over |
| Load balancing | Split traffic across models by weight |
| `litellm.cache` | Same prompt twice → second call is instant |
| `response.usage` | Token tracking without a dashboard |
| `stream=True` | Real-time streaming output |

## Files

| File | What it does |
|------|-------------|
| `notebook/llm_gateway_basics.ipynb` | Learn each concept with live Groq calls |
| `project/main.py` | FastAPI app using all gateway features together |

## Run the notebook

```bash
..\venv\Scripts\activate
jupyter notebook notebook/llm_gateway_basics.ipynb
```

## Run the FastAPI project

```bash
..\venv\Scripts\activate
copy project/.env.example project/.env    # add GROQ_API_KEY
cd project
uvicorn main:app --reload
```
