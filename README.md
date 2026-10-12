# AI Security Bootcamp

Learn how to **attack and defend LLM apps**, one hands-on project at a time.
Every module has a short notebook in simple English, with code you can run.

**Stack:** Python · Groq (`openai/gpt-oss-20b`) · LangGraph · LangChain · FastAPI · Streamlit · Guardrails AI · NeMo Guardrails · LiteLLM · PyRIT

---

## Modules

| # | Module | What you learn |
|---|--------|----------------|
| 00 | [Overview](00-overview) | Course roadmap |
| 01 | [Intro to AI Security](01-intro-ai-security) | Why LLM apps need security, and the main threat types |
| 02 | [OWASP Top 10 for LLMs](02-owasp-top10-llm) | Prompt injection scanner (8 attacks, scored out of 10) + an LLM05 improper output handling demo |
| 03 | [Guardrails](03-guardrails) | Input/output guardrails by hand, then with Guardrails AI and NeMo Guardrails, and guardrails as LangGraph nodes |
| 04 | [LLM Gateways](04-llm-gateways) | Retries, fallback models, caching and cost tracking with LiteLLM |
| 05 | [Agent Security](05-agent-security-agentops) | An agent tricked into misusing its tools (OWASP LLM06 - Excessive Agency), and how to block it |
| 06 | [LLM Evaluators](06-llm-evaluator-red-teaming) | LLM-as-a-judge answer grader + a self-correcting LangGraph loop |
| 07 | [RAG Security](07-rag-security) | Document poisoning, a verifier defense, and self-healing RAG |
| 08 | [Support Bot Security](08-support-bot-security) | Capstone: guardrail + agent trace + evaluator in one flow |
| 09 | [Secure Multi-Tenant Gateway](09-secure-multi-tenant-gateway) | BOLA/IDOR in an AI backend, the fix, and agentic BOLA |
| 10 | [Red Teaming with PyRIT](10-pyrit-red-teaming) | Attack batteries, Attack Success Rate, multi-turn attacks, XPIA |
| 11 | [Interview Checklist](11-interview-checklist) | Key AI security interview questions and answers |

---

## Setup

You need **Python 3.11** and a free [Groq API key](https://console.groq.com/keys).

```bash
git clone https://github.com/dearnidhi/ai-security-bootcamp.git
cd ai-security-bootcamp

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac / Linux

pip install -r requirements.txt

copy .env.example .env         # Windows  (Mac/Linux: cp .env.example .env)
```

Open `.env` and add your key:

```
GROQ_API_KEY=your_groq_api_key_here
```

Open any module's notebook in VS Code or Jupyter, select the **venv** kernel, and run the cells.

---

## ⚠️ Disclaimer

All attacks in this repo are for **learning and defending your own systems**.
Only test AI systems you own or have permission to test.
