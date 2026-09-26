# Guardrails wired into LangGraph

Answers the interview question: "How would you add guardrails to LangGraph?"

## What it does

Reuses `InputGuardrail` and `OutputGuardrail` from `../guardrails.py` (imported as-is,
never modified) and wraps each one as a **graph node** instead of calling them as plain
Python functions inside one big handler:

```
input -> [input_guard] --blocked--> END (refusal)
            |
          safe
            |
         [agent] -> [output_guard] --blocked--> END (fallback)
                              |
                            safe
                              |
                            END (final response)
```

A conditional edge checks the guardrail's `blocked` flag and routes straight to `END`
with a refusal if it fails, or on to the next node if it passes - the same
generate/judge-style conditional-edge pattern used in module 06's self-correcting loop
and module 09's agentic BOLA demo.

## Run

```bash
# From inside this folder
..\..\venv\Scripts\activate
copy .env.example .env    # add GROQ_API_KEY (or rely on the shared root .env)

python main.py           # console demo: 3 example messages
streamlit run app.py     # UI: type a message, pick an example, see which node blocked it
```

## Files

| File | What it does |
|------|-------------|
| `main.py` | The graph: input_guard -> agent -> output_guard, with conditional edges |
| `app.py` | Streamlit UI for `main.py`'s `run()` function |
