# 06 - LLM Evaluator

An **AI Answer Grader**: an LLM judge scores how well an AI's answer matches a reference (correct) answer, and gives a one-sentence reason.

## What it does

1. You give it a question, the AI's answer, and the correct reference answer.
2. A judge model (`openai/gpt-oss-20b`) scores the AI's answer from 0–10 and explains why.

This is the same core idea as a **faithfulness evaluator** for RAG (does the answer actually match the source of truth, or did it hallucinate?) - see `llm_evaluator_explained.ipynb` for that concept explained with examples, alongside the red-teaming methodology.

## Bonus: self-correcting answer loop (built with LangGraph)

`POST /self_correct` is a small `StateGraph`: **generate** an answer, **judge** it against the
reference, and if the score is too low, loop back to generate again with the judge's feedback
- up to 3 attempts. This is the one thing a plain chain cannot do cleanly: a **cycle**. Verified
with a forced-failure test that it retries exactly 3 times and stops, and with real questions
that it exits early once the score is good enough.

```
generate -> judge -> (score >= 8 or 3 attempts?) -> done
               ^                    |
               |____ retry __________|
```

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

Try the self-correcting loop directly:

```bash
curl -X POST http://localhost:8091/self_correct \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"What is the capital of France?\",\"reference_answer\":\"Paris\"}"
```

## Files

| File | What it does |
|------|-------------|
| `main.py` | FastAPI `/grade` endpoint (single judge call) and `/self_correct` (LangGraph generate-judge-retry loop) |
| `grader_app.py` | Streamlit UI for the grader |
| `llm_evaluator_explained.ipynb` | Faithfulness evaluation + red-teaming methodology, explained (concept only, no separate app) |
