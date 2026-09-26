"""LangGraph state machine: every guardrail is a real graph node with
conditional routing, not a sequence of function calls."""

from typing import TypedDict

from langgraph.graph import END, StateGraph

from guardrails import InputGuardrail, OutputGuardrail, ScamGuardrail, TopicGuardrail
from knowledge_base import get_rag_response, retrieve_context


class ChatState(TypedDict, total=False):
    user_input: str
    safe_input: str
    context: str
    llm_response: str
    final_response: str
    blocked: bool
    trace: list


def _step(state, name, passed):
    return state.get("trace", []) + [(name, passed)]


def input_guardrail_node(state: ChatState) -> ChatState:
    result = InputGuardrail().run(state["user_input"])
    trace = _step(state, "Input Guardrail", not result["blocked"])
    if result["blocked"]:
        return {**state, "blocked": True, "final_response": f"I can't process that. {result['reason']}", "trace": trace}
    return {**state, "safe_input": result["safe_input"], "trace": trace}


def topic_guardrail_node(state: ChatState) -> ChatState:
    result = TopicGuardrail().run(state["safe_input"])
    trace = _step(state, "Topic Guardrail", not result["blocked"])
    if result["blocked"]:
        return {**state, "blocked": True, "final_response": result["reason"], "trace": trace}
    return {**state, "trace": trace}


def scam_guardrail_node(state: ChatState) -> ChatState:
    result = ScamGuardrail().run(state["safe_input"])
    trace = _step(state, "Scam Guardrail", not result["blocked"])
    if result["blocked"]:
        return {**state, "blocked": True, "final_response": result["reason"], "trace": trace}
    return {**state, "trace": trace}


def retrieve_node(state: ChatState) -> ChatState:
    context = retrieve_context(state["safe_input"])
    trace = _step(state, "Retrieval", True)
    return {**state, "context": context, "trace": trace}


def generate_node(state: ChatState) -> ChatState:
    if not state["context"]:
        return {**state, "llm_response": "I don't have information on that — please contact your ward office.", "trace": state["trace"]}
    response = get_rag_response(state["safe_input"], state["context"])
    return {**state, "llm_response": response, "trace": state["trace"]}


def output_guardrail_node(state: ChatState) -> ChatState:
    result = OutputGuardrail().run(state["llm_response"])
    trace = _step(state, "Output Guardrail", not result["blocked"])
    return {**state, "final_response": result["final_response"], "trace": trace}


def _route(state: ChatState) -> str:
    return "blocked" if state.get("blocked") else "continue"


def build_graph():
    graph = StateGraph(ChatState)

    graph.add_node("input_guardrail", input_guardrail_node)
    graph.add_node("topic_guardrail", topic_guardrail_node)
    graph.add_node("scam_guardrail", scam_guardrail_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_node("output_guardrail", output_guardrail_node)

    graph.set_entry_point("input_guardrail")

    graph.add_conditional_edges(
        "input_guardrail", _route, {"blocked": END, "continue": "topic_guardrail"}
    )
    graph.add_conditional_edges(
        "topic_guardrail", _route, {"blocked": END, "continue": "scam_guardrail"}
    )
    graph.add_conditional_edges(
        "scam_guardrail", _route, {"blocked": END, "continue": "retrieve"}
    )
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "output_guardrail")
    graph.add_edge("output_guardrail", END)

    return graph.compile()


def ask(user_input: str) -> ChatState:
    app = build_graph()
    return app.invoke({"user_input": user_input, "trace": []})
