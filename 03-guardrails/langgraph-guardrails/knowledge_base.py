"""Tiny keyword-retrieval FAQ store + the real LLM call (Groq)."""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
load_dotenv()

GROQ_MODEL = "openai/gpt-oss-20b"
_groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

FAQ_DIR = Path(__file__).resolve().parent / "data" / "faq"

_docs = None


def _load_docs():
    global _docs
    if _docs is None:
        _docs = [
            {"id": path.stem, "text": path.read_text(encoding="utf-8")}
            for path in sorted(FAQ_DIR.glob("*.txt"))
        ]
    return _docs


def retrieve_context(query, top_k=2):
    query_words = set(re.findall(r"[a-z]+", query.lower()))
    scored = []

    for doc in _load_docs():
        doc_words = set(re.findall(r"[a-z]+", doc["text"].lower()))
        score = len(query_words & doc_words)
        if score > 0:
            scored.append((score, doc["id"], doc["text"]))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_docs = scored[:top_k]
    return "\n\n".join(f"[{doc_id}]\n{text}" for _, doc_id, text in top_docs)


def get_rag_response(question, context, max_tokens=300):
    system_prompt = (
        "You are a municipal corporation citizen helpdesk assistant. "
        "Answer ONLY using the context below. If the answer isn't in the "
        "context, say you don't have that information and suggest "
        "contacting the ward office — do not guess.\n\n"
        f"Context:\n{context}"
    )
    completion = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        max_tokens=max_tokens,
    )
    return completion.choices[0].message.content
