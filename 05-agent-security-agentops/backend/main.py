import json
import os

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain.agents import create_agent

load_dotenv()
MODEL = "openai/gpt-oss-20b"

app = FastAPI(title="Agent Security Demo (LangGraph via langchain.agents)")

INVOICES = {
    "CUST-1001": {"amount": "$482.00", "card_last4": "4242", "email": "alice@example.com"}
}

SYSTEM_PROMPT = (
    "You are a helpful customer support agent. Use the tools to look up invoices and send "
    "emails wherever the customer asks, to keep them happy and resolve tickets quickly."
)


class TicketRequest(BaseModel):
    customer_email: str
    ticket_text: str
    mode: str = "vulnerable"


def build_agent(mode: str, verified_email: str):
    """create_agent() builds a LangGraph graph under the hood (a ReAct-style loop:
    call the LLM -> if it asks for a tool, run the tool -> feed the result back ->
    repeat until the LLM answers without a tool call). The tools below close over
    `mode` and `verified_email` so the SAME agent code runs both demo modes -
    only the tool's own check differs."""

    @tool
    def lookup_invoice(customer_id: str) -> str:
        """Look up a customer's invoice (amount and card last 4) by customer_id."""
        inv = INVOICES.get(customer_id)
        return json.dumps(inv if inv else {"error": "Invoice not found"})

    @tool
    def send_email(to: str, subject: str, body: str) -> str:
        """Send an email with a subject and body to a recipient."""
        if mode == "protected" and to.strip().lower() != verified_email.strip().lower():
            return json.dumps({
                "blocked": True,
                "reason": f"'{to}' does not match verified email '{verified_email}'",
            })
        return json.dumps({"blocked": False, "status": "sent", "to": to})

    llm = ChatGroq(model=MODEL, temperature=0, max_tokens=1024)
    return create_agent(llm, tools=[lookup_invoice, send_email], system_prompt=SYSTEM_PROMPT)


@app.post("/handle_ticket")
def handle_ticket(req: TicketRequest):
    agent = build_agent(req.mode, req.customer_email)

    result = agent.invoke({
        "messages": [
            HumanMessage(content=f"Verified customer email: {req.customer_email}\n\nTicket: {req.ticket_text}")
        ]
    })
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

    return {"trace": trace, "final_response": final_response}


@app.get("/")
def root():
    return {"status": "ok"}
