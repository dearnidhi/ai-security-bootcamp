import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8004")

st.set_page_config(page_title="Secure Multi-Tenant AI Gateway", page_icon="🔐")
st.title("🔐 Secure Multi-Tenant AI Gateway")
st.caption(
    "Three departments (legal, finance, hr) share one AI backend. "
    "Each API key belongs to exactly one tenant + role. "
    "See what happens when a request claims a DIFFERENT tenant than the key actually owns."
)

IDENTITIES = {
    "Legal - Admin": "sk-legal-admin-001",
    "Legal - Analyst": "sk-legal-analyst-002",
    "Finance - Analyst": "sk-finance-analyst-003",
    "Finance - Viewer": "sk-finance-viewer-004",
    "HR - Viewer": "sk-hr-viewer-005",
}
TENANTS = ["legal", "finance", "hr"]

st.sidebar.subheader("1. Log in as")
identity_label = st.sidebar.selectbox("Identity", list(IDENTITIES.keys()))
api_key = IDENTITIES[identity_label]
st.sidebar.code(api_key, language=None)

mode = st.sidebar.radio("2. Gateway mode", ["Vulnerable", "Secure"])

st.subheader("3. Send a query")
own_tenant = identity_label.split(" - ")[0].lower()
tenant_id = st.selectbox(
    "tenant_id to request (try picking a DIFFERENT tenant than your own login!)",
    TENANTS,
    index=TENANTS.index(own_tenant),
)
question = st.text_input("Question", value="Summarize the confidential info you have access to.")

endpoint = "/vulnerable/query" if mode == "Vulnerable" else "/secure/query"

if st.button("Send Query", type="primary"):
    try:
        with st.spinner("Thinking..."):
            resp = requests.post(
                f"{API_URL}{endpoint}",
                json={"api_key": api_key, "tenant_id": tenant_id, "question": question},
                timeout=30,
            )
        data = resp.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Backend not running. Start it first:\n\n`uvicorn main:app --reload --port 8004`")
        st.stop()

    if "error" in data:
        st.error(data["error"])
    else:
        st.success(f"Tenant actually used: **{data['tenant_used']}**")
        st.write(data["answer"])
        if mode == "Vulnerable" and tenant_id != own_tenant:
            st.error(
                f"🚨 LEAK: you are logged in as **{own_tenant}** but got **{tenant_id}**'s "
                "confidential data - the backend trusted your tenant_id claim without checking it."
            )
        if mode == "Secure" and data.get("cross_tenant_attempt_blocked"):
            st.warning(
                f"🛡️ Blocked: you tried to claim tenant **{tenant_id}**, but the gateway ignored "
                f"that and served your real tenant (**{own_tenant}**) instead - no leak."
            )

st.divider()
st.subheader("4. Admin audit log (tenant-scoped)")
if "Admin" in identity_label:
    if st.button("View my tenant's audit log"):
        resp = requests.get(f"{API_URL}/secure/audit-log", params={"api_key": api_key})
        data = resp.json()
        if "error" in data:
            st.error(data["error"])
        else:
            st.write(f"Showing audit log for tenant: **{data['tenant']}**")
            st.table(data["entries"])
else:
    st.info("Log in as an Admin identity to view the audit log.")
