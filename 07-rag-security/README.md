# 07 - RAG Security

A RAG app over an expense policy knowledge base - shows what happens when a poisoned document gets into the retrieval corpus.

## What it does

4 real expense policy documents + 1 poisoned document that looks legitimate but redirects reimbursement emails to an attacker's domain.

- **Poison OFF** - AI answers correctly from real docs
- **Poison ON** - poisoned doc gets retrieved, AI gives wrong/dangerous answer
- **Verifier** - LLM judge compares the answer against a trusted reference fact and flags contradictions

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
| `main.py` | FastAPI `/ask` - retrieval, generation, LLM-judge verifier |
| `app.py` | Streamlit UI - poison toggle, answer, verifier verdict |
| `rag_security_explained.ipynb` | RAG security concepts explained simply |
