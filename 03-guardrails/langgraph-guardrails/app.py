import streamlit as st

from graph import ask

st.set_page_config(page_title="Nagar Sahayak", page_icon="🏛️")
st.title("🏛️ Nagar Sahayak — Municipal Helpdesk")
st.caption("Ask about water supply or property tax.")

if "history" not in st.session_state:
    st.session_state.history = []

if user_msg := st.chat_input("e.g. How do I request a water tanker?"):
    with st.spinner("Checking..."):
        result = ask(user_msg)
    st.session_state.history += [
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": result["final_response"], "trace": result["trace"]},
    ]

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("trace"):
            with st.expander("Guardrail checks"):
                for step, passed in msg["trace"]:
                    st.write(f"{'✅' if passed else '🚫'} {step}")
