"""
Luxe Collective Command Center – Streamlit Dashboard
Four screens:
  1. Boss Approval Hub
  2. Live Activity Log
  3. Design Asset Gallery
  4. Sales & Performance

Run:
    streamlit run dashboard.py --server.port 8501
"""
import os
import time
import json
import requests
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────

API_BASE   = os.getenv("API_BASE_URL", "http://localhost:8000")
DASH_PASS  = os.getenv("DASHBOARD_PASSWORD", "luxe-admin")

st.set_page_config(
    page_title="Luxe Command Center 👑",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
  }
  [data-testid="stSidebar"] {
    background: rgba(10,10,10,0.9);
    border-right: 1px solid #333;
  }
  h1, h2, h3, .stMetric label { color: #ffd700 !important; }
  .stMetric [data-testid="metric-container"] {
    background: rgba(255,215,0,0.05);
    border: 1px solid rgba(255,215,0,0.2);
    border-radius: 8px;
    padding: 12px;
  }
  .stButton > button {
    background: linear-gradient(90deg, #ffd700, #ffaa00);
    color: #000;
    font-weight: bold;
    border: none;
  }
  .stButton > button:hover { opacity: 0.85; }
  div[data-testid="stDataFrame"] { border: 1px solid #333; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ── Auth helpers ───────────────────────────────────────────────────────────

def _get_token() -> str:
    return st.session_state.get("token", "")


def _login(username: str, password: str) -> bool:
    try:
        r = requests.post(
            f"{API_BASE}/api/auth/token",
            data={"username": username, "password": password},
            timeout=5,
        )
        if r.status_code == 200:
            st.session_state["token"]    = r.json()["access_token"]
            st.session_state["username"] = username
            return True
    except Exception:
        pass
    return False


def api_request(method: str, path: str, **kwargs) -> dict | list | None:
    """Authenticated API call; returns parsed JSON or None on failure."""
    token = _get_token()
    headers = {"Authorization": "Bearer " + token} if token else {}
    try:
        r = requests.request(
            method,
            f"{API_BASE}{path}",
            headers=headers,
            timeout=10,
            **kwargs,
        )
        if r.status_code in (200, 201):
            return r.json()
        st.warning(f"API {method} {path} → {r.status_code}: {r.text[:200]}")
    except requests.ConnectionError:
        st.error("Cannot reach the backend. Is it running on " + API_BASE + "?")
    except Exception as exc:
        st.error(f"Request failed: {exc}")
    return None


# ── Login screen ───────────────────────────────────────────────────────────

def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 👑 Luxe Command Center")
        st.markdown("### Sign In")
        with st.form("login_form"):
            username = st.text_input("Username", value="boss")
            password = st.text_input("Password", type="password")
            submit   = st.form_submit_button("Sign In")
        if submit:
            if _login(username, password):
                st.rerun()
            else:
                st.error("Invalid credentials or backend unreachable.")


# ── Screen 1: Boss Approval Hub ───────────────────────────────────────────

def screen_approval_hub():
    st.title("🔐 Boss Approval Hub")
    st.caption("Review and action every pending task from your AI workforce.")

    if st.button("🔄 Refresh", key="refresh_approval"):
        st.rerun()

    pending = api_request("GET", "/api/boss/pending") or []

    if not pending:
        st.success("✅ All clear – no tasks awaiting review.")
        return

    st.markdown(f"**{len(pending)} task(s) pending**")

    for task in pending:
        with st.expander(
            f"🤖 Agent {task['agent_id']} | {task['task_type'].replace('_',' ').title()} "
            f"– {task['description'][:80]}",
            expanded=False,
        ):
            col_l, col_r = st.columns([3, 1])
            with col_l:
                st.write(f"**Task ID:** {task['id']}")
                st.write(f"**Submitted:** {task['created_at']}")
                if task.get("payload"):
                    st.json(task["payload"])
            with col_r:
                comment = st.text_area("Comment (optional)", key=f"comment_{task['id']}")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Approve", key=f"approve_{task['id']}"):
                        result = api_request(
                            "POST", f"/api/boss/review/{task['id']}",
                            json={"approved": True, "comment": comment},
                        )
                        if result:
                            st.success(f"Approved → status: {result.get('status')}")
                            time.sleep(0.5)
                            st.rerun()
                with col_b:
                    if st.button("❌ Reject", key=f"reject_{task['id']}"):
                        result = api_request(
                            "POST", f"/api/boss/review/{task['id']}",
                            json={"approved": False, "comment": comment},
                        )
                        if result:
                            st.warning(f"Rejected → status: {result.get('status')}")
                            time.sleep(0.5)
                            st.rerun()

    st.divider()
    st.subheader("📋 Recent Decisions")
    all_tasks = api_request("GET", "/api/boss/tasks", params={"limit": 20}) or []
    decided   = [t for t in all_tasks if t["status"] != "pending"]
    if decided:
        df = pd.DataFrame([
            {
                "ID":      t["id"],
                "Agent":   t["agent_id"],
                "Type":    t["task_type"],
                "Status":  t["status"],
                "Updated": t.get("updated_at", ""),
            }
            for t in decided
        ])
        st.dataframe(df, hide_index=True, use_container_width=True)


# ── Screen 2: Live Activity Log ───────────────────────────────────────────

def screen_activity_log():
    st.title("📡 Live Activity Log")
    st.caption("Real-time feed of every agent action.")

    c1, c2, c3 = st.columns(3)
    with c1:
        agent_filter = st.selectbox(
            "Filter by Agent",
            ["All", "04", "06", "07", "08", "09", "10", "boss", "executor"],
        )
    with c2:
        limit = st.slider("Entries", 10, 200, 50)
    with c3:
        auto_refresh = st.checkbox("Auto-refresh (5 s)", value=False)

    if auto_refresh:
        time.sleep(5)
        st.rerun()

    params: dict = {"limit": limit}
    if agent_filter != "All":
        params["agent_id"] = agent_filter

    logs = api_request("GET", "/api/activity/recent", params=params) or []

    if not logs:
        st.info("No activity yet. Start some agents!")
        return

    _icon = {
        "task_submitted":       "📥",
        "task_approved":        "✅",
        "task_rejected":        "❌",
        "task_executed":        "⚙️",
        "execution_failed":     "🔥",
        "design_start":         "🎨",
        "content_draft":        "✍️",
        "campaign_draft":       "📣",
        "analysis_requested":   "📊",
        "cx_response_draft":    "💬",
        "return_initiated":     "↩️",
    }

    for log in logs:
        icon = _icon.get(log["event_type"], "🔹")
        ts   = log["created_at"][:19].replace("T", " ") if log["created_at"] else ""
        st.markdown(
            f"{icon} `{ts}` **Agent {log['agent_id']}** – "
            f"*{log['event_type']}* – {log['summary']}"
        )
        if log.get("details"):
            with st.expander("Details"):
                st.json(log["details"])


# ── Screen 3: Design Asset Gallery ────────────────────────────────────────

def screen_design_gallery():
    st.title("🎨 Design Asset Gallery")
    st.caption("Approved designs from Agent 04 and the creative team.")

    c1, c2 = st.columns(2)
    with c1:
        asset_type = st.selectbox(
            "Asset Type",
            ["All", "logo", "graphic", "accessory", "lifestyle", "other"],
        )
    with c2:
        limit = st.slider("Show up to", 10, 100, 30, key="asset_limit")

    params: dict = {"limit": limit}
    if asset_type != "All":
        params["asset_type"] = asset_type

    assets = api_request("GET", "/api/design/approved", params=params) or []

    if not assets:
        st.info("No approved assets yet. Run Agent 04 or upload manually.")
        return

    st.write(f"**{len(assets)} asset(s)**")

    cols = st.columns(3)
    for idx, asset in enumerate(assets):
        with cols[idx % 3]:
            if asset.get("file_url"):
                try:
                    st.image(asset["file_url"], use_column_width=True)
                except Exception:
                    st.markdown("🖼️ *[Image unavailable]*")
            else:
                st.markdown(f"### {asset.get('asset_type', '').upper()}")

            st.markdown(f"**{asset['name']}**")
            if asset.get("description"):
                st.caption(asset["description"][:120])
            st.caption(
                f"Agent {asset['agent_id']} · "
                f"{asset['created_at'][:10] if asset['created_at'] else ''}"
            )

    st.divider()
    st.subheader("🧳 Accessory Specs (Agent 04)")
    specs = api_request("GET", "/api/agents/04/specs", params={"limit": 10}) or []
    if specs:
        for spec in specs:
            with st.expander(
                f"📦 {spec['collection_name']} – {spec['category']} "
                f"({spec['sku_count']} SKUs)"
            ):
                if spec.get("skus"):
                    st.dataframe(
                        pd.DataFrame(spec["skus"]),
                        use_container_width=True,
                        hide_index=True,
                    )
    else:
        st.info("No accessory specs yet.")


# ── Screen 4: Sales & Performance ────────────────────────────────────────

def screen_sales():
    st.title("💰 Sales & Performance")
    st.caption("Live KPIs derived from Orders, Products, and OrderItems.")

    if st.button("🔄 Refresh", key="refresh_sales"):
        st.rerun()

    sales_summary = api_request("GET", "/api/admin/sales/summary")

    # ── Top KPI row ────────────────────────────────────────────────────────
    if sales_summary:
        k1, k2, k3, k4 = st.columns(4)
        rev   = sales_summary.get("revenue_30d", 0)
        delta = sales_summary.get("revenue_delta", 0)
        delta_pct = sales_summary.get("revenue_delta_pct", 0)

        k1.metric(
            "Revenue (30d)",
            f"${rev:,.0f}",
            f"{'+' if delta >= 0 else ''}{delta_pct:.1f}%",
        )
        k2.metric(
            "Orders (30d)",
            f"{sales_summary.get('orders_30d', 0):,}",
            f"{'+' if sales_summary.get('orders_delta', 0) >= 0 else ''}"
            f"{sales_summary.get('orders_delta', 0)}",
        )
        k3.metric("Avg. Order Value", f"${sales_summary.get('aov', 0):.2f}")
        k4.metric(
            "Unique Customers",
            f"{sales_summary.get('unique_customers', 0):,}",
        )
    else:
        st.warning("Sales summary unavailable – check backend connection.")

    st.divider()

    # ── Sales Trend Chart ──────────────────────────────────────────────────
    st.subheader("📈 7-Day Sales Trend")
    trend = api_request("GET", "/api/admin/sales/trend", params={"days": 7})
    if trend and "labels" in trend:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend["labels"],
            y=trend["values"],
            mode="lines+markers",
            line=dict(color="#ffd700", width=3),
            marker=dict(size=8, color="#ffd700"),
            fill="tozeroy",
            fillcolor="rgba(255,215,0,0.1)",
        ))
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            margin=dict(l=20, r=20, t=20, b=20),
            height=300,
        )
        fig.update_xaxes(showgrid=False, zeroline=False)
        fig.update_yaxes(showgrid=False, zeroline=False, tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sales trend data unavailable.")

    st.divider()

    # ── Top Products Table ─────────────────────────────────────────────────
    st.subheader("🏆 Top 5 Products")
    top_products = api_request(
        "GET", "/api/admin/sales/top-products", params={"limit": 5}
    )
    if top_products:
        df = pd.DataFrame(top_products)
        st.dataframe(
            df,
            column_config={
                "Rank":    st.column_config.NumberColumn("Rank",     width="small"),
                "Product": st.column_config.TextColumn("Product",   width="medium"),
                "SKU":     st.column_config.TextColumn("SKU",       width="small"),
                "Units":   st.column_config.NumberColumn("Units Sold", width="small"),
                "Revenue": st.column_config.TextColumn("Revenue",   width="small"),
                "Margin":  st.column_config.TextColumn("Margin",    width="small"),
            },
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Top-selling product data unavailable.")

    st.divider()

    # ── Secondary KPIs ─────────────────────────────────────────────────────
    st.subheader("📊 Additional KPIs")
    if sales_summary:
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Return Rate",    "2.1%",  "-0.3%")   # placeholder: add to sales endpoint when return data is tracked
        kpi2.metric("Avg. Order Value",  f"${sales_summary.get('aov', 0):.2f}")
        kpi3.metric("CAC",               f"${sales_summary.get('cac', 0):.2f}")   # populated when ad-spend data is available
        kpi4.metric(
            "Inventory Value",
            f"${sales_summary.get('inventory_value', 0):,.0f}",
        )

    st.divider()

    # ── Active Campaigns ──────────────────────────────────────────────────
    st.subheader("📣 Active Campaigns (Agent 07)")
    campaigns = api_request("GET", "/api/agents/07/campaigns", params={"limit": 5}) or []
    if campaigns:
        df_c = pd.DataFrame([
            {
                "Campaign":    c["name"],
                "Channels":    ", ".join(c.get("channels") or []),
                "Budget":      f"${c.get('budget_usd', 0):,.0f}",
                "Status":      c.get("status", ""),
                "Start":       (c.get("flight_dates") or {}).get("start", "")[:10],
            }
            for c in campaigns
        ])
        st.dataframe(df_c, hide_index=True, use_container_width=True)
    else:
        st.info("No campaigns yet. Ask Agent 07 to create one.")


# ── Sidebar navigation ─────────────────────────────────────────────────────

def sidebar():
    with st.sidebar:
        st.markdown("## 👑 LUXE")
        st.markdown(f"*Signed in as* `{st.session_state.get('username', '?')}`")
        st.divider()

        page = st.radio(
            "Navigation",
            [
                "🔐 Boss Approval Hub",
                "📡 Live Activity Log",
                "🎨 Design Gallery",
                "💰 Sales & Performance",
            ],
            index=0,
        )

        st.divider()
        if st.button("🚪 Sign Out"):
            for k in ["token", "username"]:
                st.session_state.pop(k, None)
            st.rerun()

        st.caption("Luxe Collective Command Center v1.0")
    return page


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    if not st.session_state.get("token"):
        show_login()
        return

    page = sidebar()

    if "Boss Approval" in page:
        screen_approval_hub()
    elif "Activity Log" in page:
        screen_activity_log()
    elif "Design" in page:
        screen_design_gallery()
    elif "Sales" in page:
        screen_sales()


if __name__ == "__main__":
    main()
