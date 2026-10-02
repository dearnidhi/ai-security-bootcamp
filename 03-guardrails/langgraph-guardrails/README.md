# Guardrails wired into LangGraph

Answers the interview question: "How would you add guardrails to LangGraph?"

Each guardrail is a **graph node**. A conditional edge checks the `blocked` flag and
routes straight to `END` with a refusal, or on to the next node if it passes:

```
input_guard --blocked--> END
     |
scam_guard  --blocked--> END
     |
topic_guard --blocked--> END
     |
  answer (FAQ retrieval + Groq LLM)
     |
output_guard (PII leak check) --> END
```

## Run

```bash
..\..\venv\Scripts\activate      # GROQ_API_KEY comes from the root .env

python graph.py          # console demo: 4 example messages
streamlit run app.py     # chat UI with a per-message guardrail trace
```

## Files

| File | What it does |
|------|-------------|
| `guardrails.py` | The checks: PII masking, injection, scam, off-topic, output PII leak |
| `graph.py` | LangGraph state machine: guardrail nodes + conditional edges |
| `app.py` | Streamlit chat UI |
| `data/faq/` | 2 FAQ docs the bot answers from (water supply, property tax) |
