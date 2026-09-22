import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8091")

st.set_page_config(page_title="Simple AI Answer Grader", page_icon="📝")
st.title("📝 Simple AI Answer Grader")
st.caption(
    "Paste a question, the AI's answer, and the correct (reference) answer. "
    "An AI judge scores the answer from 0-10."
)

question = st.text_input("Question", "What is the punishment for theft under BNS?")
ai_answer = st.text_area(
    "AI's answer (the one you're grading)",
    "Theft under BNS is punished with up to 3 years in jail or a fine.",
    height=100,
)
reference_answer = st.text_area(
    "Reference answer (the correct one)",
    "Theft under Section 303 is punished with imprisonment up to 3 years, a fine, or both.",
    height=100,
)

if st.button("Grade This Answer", type="primary"):
    try:
        with st.spinner("Grading..."):
            resp = requests.post(
                f"{API_URL}/grade",
                json={
                    "question": question,
                    "ai_answer": ai_answer,
                    "reference_answer": reference_answer,
                },
                timeout=30,
            )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        st.error(
            "Can't reach the backend. Start it in another terminal first:\n\n"
            "`uvicorn main:app --reload --port 8091`"
        )
        st.stop()
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
        st.stop()

    score = data.get("score")
    if score is None:
        st.error("Couldn't parse a score. Raw response below.")
        st.code(data.get("raw_response"))
    else:
        st.metric("Score", f"{score} / 10")
        st.write("**Reason:**", data.get("reason"))
