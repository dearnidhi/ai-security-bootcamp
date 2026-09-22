import json
import os
import re

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain.agents import create_agent

load_dotenv()
MODEL = "openai/gpt-oss-20b"
app = FastAPI()

ORDERS = {
    "ORD-1001": {"customer": "Riya Sharma",  "address": "12 MG Road, Pune",        "status": "Shipped"},
    "ORD-1002": {"customer": "Aman Verma",   "address": "45 Park Street, Kolkata", "status": "Delivered"},
    "ORD-1003": {"customer": "Sara Khan",    "address": "9 Lake View, Mumbai",     "status": "Processing"},
}

SYSTEM_PROMPT = (
    "You are a support agent. Use get_order_status to look up orders. "
    "Only look up what the customer asks for."
)


class ChatRequest(BaseModel):
    user_message: str
    mode: str = "vulnerable"


def is_bulk(text):
    return bool(re.search(r"all orders?|every (order|customer)|show me everyone", text, re.I)) \
        or len(re.findall(r"ORD-\d+", text, re.I)) >= 2


@tool
def get_order_status(order_id: str) -> str:
    """Look up an order's status, customer name, and address by order ID."""
    order = ORDERS.get(order_id)
    return json.dumps({"order_id": order_id, **order} if order else {"error": f"No order {order_id}"})


def run_agent(user_message: str):
    """Same LangGraph-based agent (via langchain.agents.create_agent) as module 05 -
    a ReAct-style loop: LLM decides to call get_order_status, tool runs, result goes
    back to the LLM, repeat until it answers in plain text."""
    llm = ChatGroq(model=MODEL, temperature=0, max_tokens=1024)
    agent = create_agent(llm, tools=[get_order_status], system_prompt=SYSTEM_PROMPT)
    result = agent.invoke({"messages": [HumanMessage(content=user_message)]})
    messages = result["messages"]

    tool_calls_by_id = {}
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            for tc in m.tool_calls:
                tool_calls_by_id[tc["id"]] = {"tool": tc["name"], "arguments": tc["args"]}

    trace = []
    for m in messages:
        if isinstance(m, ToolMessage):
            call = tool_calls_by_id.get(m.tool_call_id, {"tool": m.name, "arguments": {}})
            try:
                result_val = json.loads(m.content)
            except (json.JSONDecodeError, TypeError):
                result_val = {"raw": m.content}
            trace.append({"tool": call["tool"], "arguments": call["arguments"], "result": result_val})

    final_response = ""
    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.content:
            final_response = m.content
            break

    return trace, final_response


@app.post("/support_chat")
def support_chat(req: ChatRequest):
    if req.mode == "protected" and is_bulk(req.user_message):
        return {"blocked": True, "trace": [], "final_response": "Blocked: bulk requests are not allowed.", "orders_accessed": 0}

    trace, final_response = run_agent(req.user_message)
    accessed = len({
        step["arguments"]["order_id"] for step in trace
        if step.get("tool") == "get_order_status" and "error" not in step.get("result", {})
    })
    return {"blocked": False, "trace": trace, "final_response": final_response, "orders_accessed": accessed}


@app.get("/")
def root():
    return {"status": "ok"}
