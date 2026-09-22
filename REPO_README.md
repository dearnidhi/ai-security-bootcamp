# AI Security Series

> This project is part of the **AI Security** video series on YouTube.
> **[CodeNidhi](https://www.youtube.com/@CodeNidhi)** — subscribe for more AI + dev content.

Hands-on AI Security demos built with FastAPI + Streamlit. Each folder covers one topic — real attacks, real defenses, working code you can run yourself.

## What's inside

| Folder | Topic | Backend port |
|--------|-------|-------------|
| 01-intro-ai-security | What is AI Security + real incidents (notebook only) | - |
| 02-owasp-top10-llm | OWASP Top 10 for LLMs — Prompt Injection Scanner | 8088 |
| 03-guardrails | Input, Output, Topical & Agentic Guardrails (notebook only) | - |
| 04-llm-gateways | Retries, Fallback, Caching with LiteLLM | - |
| 05-agent-security-agentops | AI agent with tools — vulnerable vs protected mode | 8001 |
| 06-llm-evaluator-red-teaming | RAG pipeline + Faithfulness evaluator | 8091 |
| 07-rag-security | RAG with poisoned document detection | 8002 |
| 08-live-demo | Full attack + defense capstone demo | 8003 |

## Setup

```bash
# 1. Create venv at root (shared by 02, 05, 06, 07, 08)
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. Add your Groq API key
copy .env.example .env    # then open .env and paste your key
```

Get a free Groq API key at [console.groq.com](https://console.groq.com)

## Running a demo

```bash
cd 02-owasp-top10-llm

# Terminal 1 — backend
uvicorn backend.main:app --reload --port 8088

# Terminal 2 — UI
streamlit run app.py
```

Change the folder name and port number for each section (see table above).
