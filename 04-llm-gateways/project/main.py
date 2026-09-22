import os
from pathlib import Path

import litellm
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from litellm import Router, completion_cost
from litellm.caching.caching import Cache
from pydantic import BaseModel

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv()  # also finds the shared .env in the project root

PRIMARY_MODEL = "groq/qwen/qwen3.8-27b"
FALLBACK_MODEL = "groq/openai/gpt-oss-20b"

litellm.cache = Cache()

router = Router(
    model_list=[
        {"model_name": "chat", "litellm_params": {"model": PRIMARY_MODEL, "timeout": 10}},
        # gpt-oss "thinks" before it answers - keep that short so the reply is never cut off
        {"model_name": "chat", "litellm_params": {"model": FALLBACK_MODEL, "timeout": 10, "reasoning_effort": "low"}},
    ],
    fallbacks=[{"chat": ["chat"]}],
    num_retries=2,
    cooldown_time=5,
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    model_used: str
    cost_usd: float | None = None


app = FastAPI(title="LLM Gateway Demo")


def response_cost(response) -> float | None:
    # LiteLLM has no price for some newer Groq models, and completion_cost() raises for them
    try:
        return completion_cost(completion_response=response)
    except Exception:
        return None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        response = router.completion(model="chat", messages=[{"role": "user", "content": req.message}], caching=True)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(
        reply=response.choices[0].message.content,
        model_used=response.model,
        cost_usd=response_cost(response),
    )


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    def tokens():
        for chunk in router.completion(model="chat", messages=[{"role": "user", "content": req.message}], stream=True):
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    return StreamingResponse(tokens(), media_type="text/plain")
