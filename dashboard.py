"""
LUXE COLLECTIVE - Live Dashboard
Streamlit frontend that reads live data from the FastAPI backend.
"""

import os

import requests
import streamlit as st

# ─── Config ───────────────────────────────────────────────────────────────────

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
ADMIN_EMAIL = os.getenv("DASHBOARD_ADMIN_EMAIL", "admin@luxecollective.com")
ADMIN_PASSWORD = os.getenv("DASHBOARD_ADMIN_PASSWORD", "admin_password")

st.set_page_config(
    page_title="LUXE COLLECTIVE Command Center",
    page_icon="👑",
    layout="wide",
)

# ─── Auth helpers ──────────────────────────────────────────────────────────────

def _get_token() -> str | None:
    """Obtain or reuse a JWT for the admin user."""
    if "auth_token" in st.session_state:
        return st.session_state["auth_token"]
    try:
        resp = requests.post(
            f"{API_BASE}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10,
        )
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            st.session_state["auth_token"] = token
            return token
    except requests.RequestException:
        pass
    return None


def api_request(method: str, path: str, **kwargs):
    """Authenticated request to the backend; returns parsed JSON or None on error."""
    token = _get_token()
    headers = {"Authorization": f"******"} if token else {}
    try:
        resp = requests.request(
            method,
            f"{API_BASE}{path}",
            headers=headers,
            timeout=10,
            **kwargs,
        )
        if resp.status_code == 200:
            return resp.json()
        st.error(f"API error {resp.status_code}: {resp.text[:200]}")
    except requests.RequestException as exc:
        st.error(f"Cannot reach backend: {exc}")
    return None


# ─── Shared CSS ────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #ffd700;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        color: #ffffff;
        margin-bottom: 1rem;
    }
    .metric-label { font-size: 0.8rem; color: #aaaaaa; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 2rem; font-weight: 700; color: #ffd700; }
    .metric-sub   { font-size: 0.75rem; color: #888888; margin-top: 4px; }

    .activity-row {
        background: #111827;
        border-left: 3px solid #ffd700;
        border-radius: 4px;
        padding: 0.5rem 0.75rem;
        margin-bottom: 6px;
        font-size: 0.85rem;
        color: #e0e0e0;
    }
    .activity-time  { color: #ffd700; font-weight: 600; margin-right: 8px; }
    .activity-agent { color: #90caf9; margin-right: 8px; }

    .design-card {
        background: #111827;
        border: 1px solid #2a2a4a;
        border-radius: 10px;
        padding: 0.75rem;
        margin-bottom: 1rem;
        text-align: center;
        color: #e0e0e0;
    }
    .design-card img { width: 100%; border-radius: 8px; object-fit: cover; height: 220px; }
    .design-title { font-weight: 600; margin-top: 0.5rem; color: #ffd700; }
    .design-meta  { font-size: 0.75rem; color: #888888; }

    .task-row {
        background: #111827;
        border: 1px solid #2a2a4a;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 8px;
        color: #e0e0e0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Title ─────────────────────────────────────────────────────────────────────

st.title("👑 LUXE COLLECTIVE Command Center")
st.caption("Real-time AI agent intelligence dashboard")

# ─── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs(
    ["🔔 Approval Hub", "🤖 Agent Activity", "🎨 Design Studio", "📊 Sales Intelligence"]
)

# ──────────────────────────────────────────────────────────────────────────────
# SCREEN 1 — Boss Agent Approval Hub
# ──────────────────────────────────────────────────────────────────────────────

with tab1:
    st.subheader("Pending Tasks")
    col_refresh, _ = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Refresh", key="refresh_tab1"):
            st.rerun()

    pending = api_request("GET", "/api/boss/pending") or []
    if not pending:
        st.info("No pending tasks — all clear. ✅")
    for task in pending:
        with st.expander(
            f"[{task['agent_id']}] {task['description']} — {task.get('task_type', '')}",
            expanded=False,
        ):
            st.json(task.get("payload", {}))
            col_a, col_r, col_fb = st.columns([1, 1, 3])
            feedback_key = f"fb_{task['id']}"
            with col_fb:
                feedback = st.text_input("Feedback (optional)", key=feedback_key)
            with col_a:
                if st.button("✅ Approve", key=f"approve_{task['id']}"):
                    result = api_request(
                        "POST",
                        f"/api/boss/tasks/{task['id']}/approve",
                        params={"feedback": feedback or "Approved by Boss Agent."},
                    )
                    if result:
                        st.success("Task approved!")
                        st.rerun()
            with col_r:
                if st.button("❌ Reject", key=f"reject_{task['id']}"):
                    result = api_request(
                        "POST",
                        f"/api/boss/tasks/{task['id']}/reject",
                        params={"feedback": feedback or "Rejected by Boss Agent."},
                    )
                    if result:
                        st.warning("Task rejected.")
                        st.rerun()

    st.divider()
    st.subheader("Recently Reviewed")
    reviewed = api_request("GET", "/api/boss/tasks", params={"status": "approved"}) or []
    reviewed += api_request("GET", "/api/boss/tasks", params={"status": "rejected"}) or []
    reviewed.sort(key=lambda t: t.get("reviewed_at") or "", reverse=True)
    for task in reviewed[:10]:
        icon = "✅" if task["status"] == "approved" else "❌"
        st.markdown(
            f'<div class="task-row">{icon} <b>[{task["agent_id"]}]</b> '
            f'{task["description"]} — <i>{task.get("boss_feedback", "")}</i></div>',
            unsafe_allow_html=True,
        )

# ──────────────────────────────────────────────────────────────────────────────
# SCREEN 2 — Live Agent Activity Stream
# ──────────────────────────────────────────────────────────────────────────────

with tab2:
    st.subheader("Live Agent Activity Stream")
    col_r2, col_limit, _ = st.columns([1, 2, 5])
    with col_r2:
        if st.button("🔄 Refresh", key="refresh_tab2"):
            st.rerun()
    with col_limit:
        limit = st.slider("Entries", min_value=5, max_value=100, value=20, key="activity_limit")

    activity_data = api_request("GET", "/api/activity/recent", params={"limit": limit})
    if activity_data is None:
        st.warning("Unable to load activity feed.")
    elif not activity_data:
        st.info("No activity recorded yet.")
    else:
        for activity in activity_data:
            st.markdown(
                f'<div class="activity-row">'
                f'<span class="activity-time">{activity["time"]}</span>'
                f'<span class="activity-agent">Agent {activity["agent"]}</span>'
                f'{activity["action"]}'
                f'</div>',
                unsafe_allow_html=True,
            )

# ──────────────────────────────────────────────────────────────────────────────
# SCREEN 3 — Product Design Studio Feed
# ──────────────────────────────────────────────────────────────────────────────

with tab3:
    st.subheader("Approved Design Assets")
    if st.button("🔄 Refresh", key="refresh_tab3"):
        st.rerun()

    designs = api_request("GET", "/api/design/approved")
    if designs is None:
        st.warning("Unable to load approved designs.")
    elif not designs:
        st.info("No approved designs yet. Approve design tasks in the Approval Hub first.")
    else:
        cols = st.columns(3)
        for idx, design in enumerate(designs):
            with cols[idx % 3]:
                img_url = None
                data = design.get("asset_data", {})
                if design.get("agent_id") == "02":
                    variations = data.get("variations", [])
                    if variations:
                        img_url = variations[0].get("mockup_url")
                elif design.get("agent_id") == "03":
                    graphics = data.get("designs", [])
                    if graphics:
                        img_url = graphics[0].get("image_url")
                if not img_url:
                    img_url = (
                        "https://via.placeholder.com/400x400/1a1a1a/ffd700?text=NO+IMG"
                    )
                st.markdown(
                    f'<div class="design-card">'
                    f'<img src="{img_url}" alt="design"/>'
                    f'<div class="design-title">{design.get("asset_type", "Design").title()}</div>'
                    f'<div class="design-meta">Agent {design.get("agent_id")} · '
                    f'Task #{design.get("task_id")}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

# ──────────────────────────────────────────────────────────────────────────────
# SCREEN 4 — Sales & Performance Intelligence
# ──────────────────────────────────────────────────────────────────────────────

with tab4:
    st.subheader("Sales & Performance Intelligence")
    if st.button("🔄 Refresh", key="refresh_tab4"):
        st.rerun()

    # ── KPI Cards ──────────────────────────────────────────────────────────────
    sales_summary = api_request("GET", "/api/admin/sales/summary")
    if sales_summary:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-label">Revenue Today</div>'
                f'<div class="metric-value">${sales_summary["revenue_today"]:,.2f}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-label">Conversion Rate</div>'
                f'<div class="metric-value">{sales_summary["conversion_rate"]}%</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-label">Top Product (7d)</div>'
                f'<div class="metric-value" style="font-size:1.1rem">'
                f'{sales_summary["top_product"]}</div>'
                f'<div class="metric-sub">{sales_summary["top_units"]} units · '
                f'${sales_summary["top_revenue"]:,.2f}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-label">ROAS</div>'
                f'<div class="metric-value">{sales_summary["roas"]}×</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.warning("Unable to load sales summary.")

    st.divider()

    # ── Sales Trend Chart ──────────────────────────────────────────────────────
    trend_days = st.slider("Trend window (days)", min_value=3, max_value=30, value=7, key="trend_days")
    trend = api_request("GET", "/api/admin/sales/trend", params={"days": trend_days})
    if trend:
        import pandas as pd

        df_trend = pd.DataFrame({"Date": trend["labels"], "Revenue ($)": trend["values"]})
        df_trend = df_trend.set_index("Date")
        st.line_chart(df_trend)
    else:
        st.warning("Unable to load sales trend.")

    st.divider()

    # ── Top Products Table ──────────────────────────────────────────────────────
    st.subheader("Top Products (Last 7 Days)")
    top_products = api_request("GET", "/api/admin/sales/top-products", params={"limit": 10})
    if top_products:
        import pandas as pd

        st.dataframe(pd.DataFrame(top_products), use_container_width=True, hide_index=True)
    else:
        st.warning("Unable to load top products.")
