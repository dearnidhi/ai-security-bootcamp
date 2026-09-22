import json
import os
import re

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-20b"

app = FastAPI(title="Simple AI Answer Grader")


class GradeRequest(BaseModel):
    question: str
    ai_answer: str
    reference_answer: str


@app.post("/grade")
def grade(req: GradeRequest):
    prompt = (
        "You are a strict grader. Compare the AI's answer to the reference (correct) answer "
        "for the given question. Score the AI's answer from 0 to 10 based on how factually "
        "correct and complete it is compared to the reference. Then give a one-sentence reason.\n\n"
        f"Question: {req.question}\n\n"
        f"Reference (correct) answer: {req.reference_answer}\n\n"
        f"AI's answer to grade: {req.ai_answer}\n\n"
        'Respond with ONLY JSON: {"score": <int 0-10>, "reason": "<one sentence>"}'
    )

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        reasoning_effort="low",
        max_completion_tokens=1024,
    )
    raw = completion.choices[0].message.content or ""
    match = re.search(r"\{.*\}", raw, re.DOTALL)

    try:
        parsed = json.loads(match.group(0)) if match else {}
        score, reason = parsed.get("score"), parsed.get("reason")
    except json.JSONDecodeError:
        score, reason = None, raw

    return {"score": score, "reason": reason, "raw_response": raw}


@app.get("/")
def root():
    return {"status": "ok"}
