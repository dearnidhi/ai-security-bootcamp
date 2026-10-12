import os
import re
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-20b"

app = FastAPI(title="LLM05 - Improper Output Handling")


class SummarizeRequest(BaseModel):
    review: str


def summarize(review: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "Summarize the review and keep its formatting."
            },
            {
                "role": "user",
                "content": f"Summarize this review:\n\n{review}"
            }
        ],
        temperature=0,
        max_completion_tokens=512
    )
    return response.choices[0].message.content or "TEST SUMMARY"


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


@app.post("/vulnerable/summarize")
def vulnerable(req: SummarizeRequest):
    return {"summary": summarize(req.review)}


@app.post("/secure/summarize")
def secure(req: SummarizeRequest):
    return {"summary": strip_html(summarize(req.review))}


@app.get("/")
def root():
    return {"status": "ok"}