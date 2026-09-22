# 06 — LLM Evaluator

An **AI Answer Grader**: an LLM judge scores how well an AI's answer matches a reference (correct) answer, and gives a one-sentence reason.

## What it does

1. You give it a question, the AI's answer, and the correct reference answer.
2. A judge model (`openai/gpt-oss-20b`) scores the AI's answer from 0–10 and explains why.

This is the same core idea as a **faithfulness evaluator** for RAG (does the answer actually match the source of truth, or did it hallucinate?) — see `llm_evaluator_explained.ipynb` for that concept explained with examples, alongside the red-teaming methodology.

## Run

```bash
# From inside this folder
..\venv\Scripts\activate
copy .env.example .env    # add GROQ_API_KEY

# Terminal 1
uvicorn main:app --reload --port 8091

# Terminal 2
streamlit run grader_app.py
```

## Files

| File | What it does |
|------|-------------|
| `main.py` | FastAPI `/grade` endpoint — the judge model call |
| `grader_app.py` | Streamlit UI for the grader |
| `llm_evaluator_explained.ipynb` | Faithfulness evaluation + red-teaming methodology, explained (concept only, no separate app) |
