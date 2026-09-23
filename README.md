# AI Security Series

> Hands-on AI Security course for AI/ML engineers. Real attacks, real defenses, working code, built with FastAPI + Streamlit, powered entirely by **Groq**.
>
> Part of the **AI Security** video series on YouTube: **[CodeNidhi](https://www.youtube.com/@CodeNidhi)**. Subscribe for the full walkthroughs.

Each folder covers one topic. Every demo is runnable, not just theory: attack it, then defend it.

## What's inside

| # | Topic | What you'll do |
|---|-------|-----------------|
| 00 | Overview | How this course is structured, setup, study order |
| 01 | Intro to AI Security | What AI security is, plus real-world incidents |
| 02 | OWASP Top 10 for LLMs | Score a system prompt against 8 real attacks (naive vs hardened) |
| 03 | Guardrails | Part 1: build guardrails by hand. Part 2: the same with **Guardrails AI** and **NeMo Guardrails** |
| 04 | LLM Gateways | Retries, fallback, caching, cost tracking with **LiteLLM** |
| 05 | Agentic AI Security | An agent with tools gets tricked into leaking data: vulnerable vs protected, built with **LangGraph** |
| 06 | LLM Evaluation | An LLM-as-judge grader, plus faithfulness evaluation concepts |
| 07 | RAG Security | A poisoned document silently redirects a RAG answer |
| 08 | Capstone | Guardrail, agent and evaluator in one request (LangGraph) |
| 09 | Secure Multi-Tenant Architecture | BOLA/IDOR case study: one tenant's key reads another tenant's data |
| 10 | Red Teaming with PyRIT | Automated attacks, converters, scorers, Attack Success Rate |
| 11 | Interview Checklist | Every question from every module, in one place |

## Setup

```bash
git clone <this-repo-url>
cd ai-security-series

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
copy .env.example .env         # add your GROQ_API_KEY
```

Get a free key: https://console.groq.com/keys

Modules 03 (Part 2) and 11 install larger libraries, so the first `pip install` takes a few minutes.

## Running a module

Notebook-only modules (01, 03 Part 1, 06, 07): just open the `.ipynb` and run top to bottom.

App modules (02, 05, 06, 07, 08, 10): two terminals.

```bash
# Terminal 1: backend
uvicorn main:app --reload --port <see that module's README>

# Terminal 2: frontend
streamlit run app.py
```

Every module has its own `README.md` with exact ports and commands.

## Stack

Python, FastAPI, Streamlit, Groq, LangGraph, LiteLLM, PyRIT, Guardrails AI, NeMo Guardrails

## Series

Part of the **AI Security** video series on YouTube: [CodeNidhi](https://www.youtube.com/@CodeNidhi). Subscribe for the full walkthroughs.

## License

MIT
