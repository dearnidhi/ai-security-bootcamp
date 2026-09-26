import streamlit as st

from graph import ask

st.set_page_config(page_title="Nagar Sahayak", page_icon="🏛️")
st.title("🏛️ Nagar Sahayak — Municipal Helpdesk")
st.caption("Ask about water supply, garbage collection, property tax, or birth/death certificates.")

if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant" and msg.get("trace"):
            with st.expander("How this was checked"):
                for step, passed in msg["trace"]:
                    st.write(f"{'✅' if passed else '🚫'} {step}")

user_msg = st.chat_input("e.g. How do I complain about a missed garbage pickup?")

if user_msg:
    st.session_state.history.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.write(user_msg)

    with st.chat_message("assistant"):
        with st.spinner("Checking..."):
            final_state = ask(user_msg)
        st.write(final_state["final_response"])
        with st.expander("How this was checked"):
            for step, passed in final_state.get("trace", []):
                st.write(f"{'✅' if passed else '🚫'} {step}")

    st.session_state.history.append({
        "role": "assistant",
        "content": final_state["final_response"],
        "trace": final_state.get("trace", []),
    })
