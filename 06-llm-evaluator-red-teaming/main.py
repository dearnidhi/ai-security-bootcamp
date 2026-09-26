import json
import os
import re
from typing import TypedDict

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import END, StateGraph

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-20b"

app = FastAPI(title="Simple AI Answer Grader")


def ask_groq(prompt: str) -> str:
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        reasoning_effort="low",
        max_completion_tokens=1024,
    )
    return completion.choices[0].message.content or ""


def parse_score(raw: str):
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    try:
        parsed = json.loads(match.group(0)) if match else {}
        return parsed.get("score"), parsed.get("reason")
    except json.JSONDecodeError:
        return None, raw


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
    raw = ask_groq(prompt)
    score, reason = parse_score(raw)
    return {"score": score, "reason": reason, "raw_response": raw}


# ---------------------------------------------------------------------------
# Bonus: a LangGraph loop that GENERATES an answer, JUDGES it, and RETRIES with
# feedback if the score is low - this is the one thing a plain chain cannot do
# cleanly (a cycle), so it is a genuine reason to reach for LangGraph here.
# ---------------------------------------------------------------------------

MAX_ATTEMPTS = 3
PASS_SCORE = 8


class SelfCorrectState(TypedDict):
    question: str
    reference_answer: str
    answer: str
    score: int | None
    reason: str
    attempts: int
    history: list


def generate_node(state: SelfCorrectState) -> SelfCorrectState:
    if state["attempts"] == 0:
        prompt = f"Answer this question concisely: {state['question']}"
    else:
        prompt = (
            f"Answer this question concisely: {state['question']}\n\n"
            f"Your previous answer was: {state['answer']}\n"
            f"A grader said: {state['reason']}\n"
            "Write a better answer that fixes this feedback."
        )
    answer = ask_groq(prompt)
    return {**state, "answer": answer, "attempts": state["attempts"] + 1}


def judge_node(state: SelfCorrectState) -> SelfCorrectState:
    prompt = (
        "You are a strict grader. Compare the AI's answer to the reference (correct) answer "
        "for the given question. Score the AI's answer from 0 to 10. Then give a one-sentence reason.\n\n"
        f"Question: {state['question']}\n\n"
        f"Reference (correct) answer: {state['reference_answer']}\n\n"
        f"AI's answer to grade: {state['answer']}\n\n"
        'Respond with ONLY JSON: {"score": <int 0-10>, "reason": "<one sentence>"}'
    )
    raw = ask_groq(prompt)
    score, reason = parse_score(raw)
    history = state["history"] + [{"attempt": state["attempts"], "answer": state["answer"],
                                    "score": score, "reason": reason}]
    return {**state, "score": score, "reason": reason or "", "history": history}


def route_after_judge(state: SelfCorrectState) -> str:
    if (state["score"] or 0) >= PASS_SCORE or state["attempts"] >= MAX_ATTEMPTS:
        return "done"
    return "retry"


_graph_builder = StateGraph(SelfCorrectState)
_graph_builder.add_node("generate", generate_node)
_graph_builder.add_node("judge", judge_node)
_graph_builder.set_entry_point("generate")
_graph_builder.add_edge("generate", "judge")
_graph_builder.add_conditional_edges("judge", route_after_judge, {"retry": "generate", "done": END})
self_correct_graph = _graph_builder.compile()


class SelfCorrectRequest(BaseModel):
    question: str
    reference_answer: str


@app.post("/self_correct")
def self_correct(req: SelfCorrectRequest):
    result = self_correct_graph.invoke({
        "question": req.question,
        "reference_answer": req.reference_answer,
        "answer": "",
        "score": None,
        "reason": "",
        "attempts": 0,
        "history": [],
    })
    return {
        "final_answer": result["answer"],
        "final_score": result["score"],
        "attempts_used": result["attempts"],
        "history": result["history"],
    }


@app.get("/")
def root():
    return {"status": "ok"}
