import os
from pathlib import Path
from typing import TypedDict

import litellm
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from groq import Groq
from langgraph.graph import END, StateGraph
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


# ---------------------------------------------------------------------------
# Bonus: the same fallback idea, expressed as a LangGraph routing graph instead
# of LiteLLM's Router. LiteLLM handles this at the infra layer (retries, timeouts,
# provider-agnostic calls); a graph is how you'd add the SAME decision at the
# orchestration layer, e.g. when the routing logic depends on more than "did the
# HTTP call fail" - like a content check, a cost budget, or which tool ran first.
# ---------------------------------------------------------------------------

_groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
_PRIMARY_MODEL_NAME = "qwen/qwen3.8-27b"
_FALLBACK_MODEL_NAME = "openai/gpt-oss-20b"


class RouteState(TypedDict):
    message: str
    simulate_primary_failure: bool
    reply: str
    model_used: str
    primary_error: str


def try_primary(state: RouteState) -> RouteState:
    if state["simulate_primary_failure"]:
        # fault injection for the demo - a real failure would look the same to the router
        return {**state, "primary_error": "simulated: primary model unavailable"}
    completion = _groq_client.chat.completions.create(
        model=_PRIMARY_MODEL_NAME,
        messages=[{"role": "user", "content": state["message"]}],
        temperature=0,
    )
    return {**state, "reply": completion.choices[0].message.content or "",
            "model_used": _PRIMARY_MODEL_NAME, "primary_error": ""}


def route_after_primary(state: RouteState) -> str:
    return "fallback" if state["primary_error"] else "done"


def try_fallback(state: RouteState) -> RouteState:
    completion = _groq_client.chat.completions.create(
        model=_FALLBACK_MODEL_NAME,
        messages=[{"role": "user", "content": state["message"]}],
        temperature=0,
        reasoning_effort="low",
        max_completion_tokens=512,
    )
    return {**state, "reply": completion.choices[0].message.content or "",
            "model_used": _FALLBACK_MODEL_NAME}


_route_graph_builder = StateGraph(RouteState)
_route_graph_builder.add_node("primary", try_primary)
_route_graph_builder.add_node("fallback", try_fallback)
_route_graph_builder.set_entry_point("primary")
_route_graph_builder.add_conditional_edges("primary", route_after_primary, {"fallback": "fallback", "done": END})
_route_graph_builder.add_edge("fallback", END)
route_graph = _route_graph_builder.compile()


class GraphRouteRequest(BaseModel):
    message: str
    simulate_primary_failure: bool = False


@app.post("/chat/graph_route")
def chat_graph_route(req: GraphRouteRequest):
    result = route_graph.invoke({
        "message": req.message,
        "simulate_primary_failure": req.simulate_primary_failure,
        "reply": "", "model_used": "", "primary_error": "",
    })
    return {
        "reply": result["reply"],
        "model_used": result["model_used"],
        "fell_back": bool(result["primary_error"]),
    }
