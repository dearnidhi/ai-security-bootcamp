# LLM05 - Improper Output Handling

A review summarizer that shows what happens when an app trusts an LLM's output blindly.

## What it does

One review contains a "signature" the reviewer asks to be kept as-is:

```
<img src=x onerror="alert('XSS-LLM05')">
```

The model is a good assistant - it keeps the formatting exactly as asked. **The model did
nothing wrong here.** What happens next depends entirely on what the app does with that text.

- **Vulnerable mode**: the raw summary is rendered with `st.markdown(summary, unsafe_allow_html=True)`.
  The `<img>` tag's `onerror` handler fires as real JavaScript in your browser - a stored XSS,
  and the LLM was the delivery mechanism.
- **Secure mode**: the backend strips all HTML tags from the model's output before it is ever
  returned. There is nothing left to render, so nothing executes.

This is why OWASP calls it *Improper Output Handling*, not "the model got hacked" - the fix is
entirely on the application side: never trust generated text enough to render it as markup
without sanitizing it first.

## Run

```bash
# From inside this folder
..\..\venv\Scripts\activate
copy .env.example .env    # add GROQ_API_KEY (or rely on the shared root .env)

# Terminal 1
uvicorn main:app --reload --port 8089

# Terminal 2
streamlit run app.py
```

## Try it yourself (curl)

```bash
# Vulnerable - the <img> tag survives in the response
curl -X POST http://localhost:8089/vulnerable/summarize -H "Content-Type: application/json" -d "{}"

# Secure - the tag is stripped before it ever leaves the backend
curl -X POST http://localhost:8089/secure/summarize -H "Content-Type: application/json" -d "{}"
```

## Files

| File | What it does |
|------|-------------|
| `main.py` | FastAPI: summarizes a review, vulnerable endpoint returns raw output, secure endpoint strips HTML |
| `app.py` | Streamlit UI: pick a mode, watch the alert fire (or not) in your browser |
