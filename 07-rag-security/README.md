# 07 - RAG Security

A RAG app over an expense policy knowledge base - shows what happens when a poisoned document gets into the retrieval corpus.

## What it does

4 real expense policy documents + 1 poisoned document that looks legitimate but redirects reimbursement emails to an attacker's domain.

- **Poison OFF** - AI answers correctly from real docs
- **Poison ON** - poisoned doc gets retrieved, AI gives wrong/dangerous answer
- **Verifier** - LLM judge compares the answer against a trusted reference fact and flags contradictions

## Bonus: Corrective RAG (built with LangGraph, `/ask/corrective`)

Plain retrieve -> generate -> verify is a straight line. `/ask/corrective` adds a **cycle**:
if the verifier flags a contradiction, the pipeline finds which document contains the wrong
email address (by comparing it to the canonical fact, not by asking the LLM to quote a
snippet - LLMs paraphrase, so exact-text matching against the source doc is unreliable),
drops that document, and retries generation with the smaller, clean context.

```
retrieve -> generate -> verify --contradicts--> filter out bad doc -> generate (retry)
                            |
                          clean
                            |
                          done
```

With poison ON: attempt 1 answers wrong (poisoned doc still in context, `contradicts: true`),
the poisoned doc gets filtered out, attempt 2 answers correctly (`contradicts: false`) - the
pipeline heals itself without a human ever intervening. Up to 2 attempts.

```bash
curl -X POST http://localhost:8002/ask/corrective -H "Content-Type: application/json" -d "{\"include_poison\": true}"
```

## Run

```bash
# From inside this folder
..\venv\Scripts\activate
copy .env.example .env    # add GROQ_API_KEY

# Terminal 1
uvicorn main:app --reload --port 8002

# Terminal 2
streamlit run app.py
```

## Files

| File | What it does |
|------|-------------|
| `main.py` | FastAPI `/ask` (retrieval, generation, LLM-judge verifier) and `/ask/corrective` (LangGraph self-healing loop) |
| `app.py` | Streamlit UI - poison toggle, answer, verifier verdict |
| `rag_security_explained.ipynb` | RAG security concepts explained simply |
