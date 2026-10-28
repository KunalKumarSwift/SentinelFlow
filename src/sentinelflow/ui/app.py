# Streamlit's table APIs are typed against optional pandas types strict pyright cannot see.
# pyright: reportUnknownMemberType=false
"""Streamlit pages: incidents, approvals inbox and audit trail.

    uv run --group ui streamlit run src/sentinelflow/ui/app.py

Every action goes through the REST API with the signed-in user's token, so the API's
RBAC, ABAC, separation-of-duties and audit rules apply exactly as for any other client.
"""

import httpx
import streamlit as st

from sentinelflow.ui.client import ApiError, SentinelFlowClient, dev_token
from sentinelflow.ui.views import approval_rows, incident_rows

ROLES = ["soc-analyst-l1", "soc-analyst-l2", "incident-commander", "auditor", "executive"]


def _sign_in() -> SentinelFlowClient:
    st.sidebar.header("Sign in (dev tokens)")
    api = st.sidebar.text_input("API", "http://127.0.0.1:8000")
    subject = st.sidebar.text_input("User", "u-analyst")
    role = st.sidebar.selectbox("Role", ROLES, index=2)
    identity = {"subject": subject, "tenant_id": "acme", "team": "soc-emea", "roles": [role]}
    http = httpx.Client(base_url=api, timeout=10)
    return SentinelFlowClient(http, dev_token(http, identity))


def _incidents(client: SentinelFlowClient) -> None:
    st.subheader("Incidents")
    st.dataframe(incident_rows(client.incidents()), width="stretch")


def _approvals(client: SentinelFlowClient) -> None:
    st.subheader("Approvals inbox")
    approvals = client.approvals()
    st.dataframe(approval_rows(approvals), width="stretch")
    if not approvals:
        return
    chosen = st.selectbox("Approval", [a.id for a in approvals])
    reason = st.text_input("Reason (5+ characters)", "evidence reviewed")
    approve, reject = st.columns(2)
    for column, label, approved in ((approve, "Approve", True), (reject, "Reject", False)):
        if column.button(label):
            client.decide(chosen, approved=approved, reason=reason)
            st.success(f"{label} recorded for {chosen}")


def _audit(client: SentinelFlowClient) -> None:
    st.subheader("Audit trail")
    result = client.verify()
    st.metric("Chain verified", "yes" if result.ok else f"broken at {result.first_bad_seq}")
    st.dataframe([e.model_dump() for e in client.audit(after_seq=0, limit=200)])


def main() -> None:
    """Render the app for the signed-in user."""
    st.set_page_config(page_title="SentinelFlow", layout="wide")
    st.title("SentinelFlow")
    client = _sign_in()
    for page in (_incidents, _approvals, _audit):
        try:
            page(client)
        except ApiError as error:  # e.g. an L1 analyst opening the approvals inbox
            st.info(f"Not available for this role ({error})")


main()
