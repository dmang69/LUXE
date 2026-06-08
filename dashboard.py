from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components

API_BASE_URL = "http://localhost:8000"
REFRESH_INTERVAL = 5


AGENT_STATUS = {
    "Agent 01": "Monitoring",
    "Agent 02": "Generating logos",
    "Agent 03": "Creating designs",
    "Agent 04": "Designing accessories",
    "Agent 05": "Sourcing vendors",
    "Agent 06": "Maintaining store",
    "Agent 07": "Running campaigns",
    "Agent 08": "Creating content",
    "Agent 09": "Analyzing data",
    "Agent 10": "Supporting customers",
}


APPROVED_DESIGNS = [
    {
        "id": "des_001",
        "agent": "02",
        "name": "Ankh & Lotus Fusion",
        "description": "Egyptian-inspired logo combining the ankh symbol with lotus flower, optimized for chest print on organic cotton hoodies",
        "preview": "ANKH LOTUS",
        "tags": ["Egyptian", "Ankh", "Lotus", "Gold on Black"],
    },
    {
        "id": "des_002",
        "agent": "02",
        "name": "Valknut Triad",
        "description": "Norse interlocking triangles symbolizing interconnectedness, designed for all-over print on lightweight summer tees",
        "preview": "VALKNUT",
        "tags": ["Norse", "Valknut", "Triad", "Silver on Navy"],
    },
    {
        "id": "des_003",
        "agent": "03",
        "name": "Celtic Chest Emblem",
        "description": "Intricate knotwork pattern designed for left chest placement on premium tees, featuring seamless repeat",
        "preview": "CELTIC CHEST",
        "tags": ["Celtic", "Knotwork", "Chest", "Emerald on Cream"],
    },
    {
        "id": "des_004",
        "agent": "03",
        "name": "Scarab Back Piece",
        "description": "Large Egyptian scarab beetle design for full back jackets, with hieroglyphic border detailing",
        "preview": "SCARAB BACK",
        "tags": ["Egyptian", "Scarab", "Back", "Gold on Charcoal"],
    },
    {
        "id": "des_005",
        "agent": "02",
        "name": "Nordic Compass",
        "description": "Vegvisir Icelandic compass symbol for navigation, perfect for sleeve placement on denim jackets",
        "preview": "VEGVISIR",
        "tags": ["Norse", "Vegvisir", "Sleeve", "Copper on Olive"],
    },
    {
        "id": "des_006",
        "agent": "03",
        "name": "Lotus All-Over",
        "description": "Delicate lotus flower pattern for all-over print on silk camisoles, featuring gradient color transitions",
        "preview": "LOTUS ALL-OVER",
        "tags": ["Egyptian", "Lotus", "All-Over", "Pink to White Gradient"],
    },
]


ACTIVITIES = [
    (15, "Agent 02", "Generated 3 new Egyptian hieroglyph logo variations for Summer Collection"),
    (42, "Agent 03", "Completed Celtic knotwork pattern for Nemeton Hoodie (85% complete)"),
    (58, "Agent 05", "Received quote from Turkish DTG printer: $8.20/unit, 4-day turnaround"),
    (72, "Agent 07", "Launched Instagram campaign for Anubis Ankhes collection (Reach: 12.4K)"),
    (105, "Agent 09", "Updated sales forecast: Q3 revenue projected +18% vs target"),
    (150, "Agent 04", "Finalized tech specs for Scarab Wallet line (Production ready)"),
    (185, "Agent 08", "Wrote product description for Nemeton Hoodie (SEO optimized)"),
    (220, "Agent 10", "Resolved 3 customer inquiries (Satisfaction: 4.8/5)"),
]


TOP_PRODUCTS = [
    {"Rank": 1, "Product": "Nemeton Hoodie", "SKU": "NMD-HT-001", "Units": 42, "Revenue": "$1,050", "Margin": "68%"},
    {"Rank": 2, "Product": "Anubis Ankhes", "SKU": "ANK-AK-002", "Units": 38, "Revenue": "$1,520", "Margin": "72%"},
    {"Rank": 3, "Product": "Valknut Tee", "SKU": "VLK-TE-003", "Units": 35, "Revenue": "$700", "Margin": "65%"},
    {"Rank": 4, "Product": "Celtic Chest Emblem Tee", "SKU": "CLT-CE-004", "Units": 28, "Revenue": "$560", "Margin": "63%"},
    {"Rank": 5, "Product": "Scarab Back Jacket", "SKU": "SCB-JK-005", "Units": 22, "Revenue": "$1,760", "Margin": "75%"},
]


def api_request(method: str, endpoint: str, data: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> Any:
    try:
        response = requests.request(
            method=method,
            url=f"{API_BASE_URL}{endpoint}",
            json=data,
            params=params,
            timeout=5,
        )
        response.raise_for_status()
        if not response.content:
            return {}
        content_type = response.headers.get("content-type", "")
        return response.json() if "application/json" in content_type else response.text
    except requests.exceptions.RequestException as exc:
        st.error(f"API Error: {exc}")
        return None



def format_currency(amount: float) -> str:
    return f"${amount:,.2f}"



def format_percent(value: float) -> str:
    return f"{value:+.1f}%"



def render_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: linear-gradient(180deg, #0b0b0f 0%, #12121a 45%, #181824 100%);
                color: #f5f0d8;
            }
            [data-testid="stSidebar"] {
                background: #0f1017;
                border-right: 1px solid rgba(255, 215, 0, 0.15);
            }
            .luxe-shell {
                padding: 0.5rem 0 1rem 0;
            }
            .hero-card, .panel-card, .activity-card, .design-card, .metric-card {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 215, 0, 0.18);
                border-radius: 18px;
                box-shadow: 0 12px 30px rgba(0, 0, 0, 0.20);
            }
            .hero-card {
                padding: 1.5rem;
                margin-bottom: 1rem;
                background: radial-gradient(circle at top right, rgba(255, 215, 0, 0.14), rgba(255, 255, 255, 0.02));
            }
            .hero-card h1, .panel-title, .design-card h4 {
                color: #ffd700;
                margin: 0;
            }
            .hero-card p, .muted {
                color: #d9d1b3;
            }
            .status-pill, .tag-pill {
                display: inline-block;
                padding: 0.2rem 0.6rem;
                border-radius: 999px;
                font-size: 0.75rem;
                margin: 0.1rem 0.3rem 0.1rem 0;
            }
            .status-pill {
                background: rgba(0, 255, 136, 0.12);
                color: #8cffc4;
                border: 1px solid rgba(0, 255, 136, 0.20);
            }
            .tag-pill {
                background: rgba(255, 215, 0, 0.12);
                color: #ffd86a;
                border: 1px solid rgba(255, 215, 0, 0.20);
            }
            .agent-row {
                padding: 0.55rem 0.75rem;
                margin-bottom: 0.5rem;
                border-radius: 14px;
                background: rgba(255, 255, 255, 0.025);
                border: 1px solid rgba(255, 215, 0, 0.10);
            }
            .metric-card {
                padding: 1rem 1.1rem;
                min-height: 112px;
            }
            .metric-label {
                color: #c9bf95;
                font-size: 0.9rem;
                margin-bottom: 0.4rem;
            }
            .metric-value {
                color: #ffffff;
                font-size: 1.8rem;
                font-weight: 700;
                margin-bottom: 0.2rem;
            }
            .metric-delta-positive, .metric-delta-negative {
                font-size: 0.95rem;
                font-weight: 600;
            }
            .metric-delta-positive { color: #8cffc4; }
            .metric-delta-negative { color: #ff8b8b; }
            .activity-card, .design-card {
                padding: 1rem;
                margin-bottom: 0.75rem;
            }
            .preview-box {
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 180px;
                border-radius: 16px;
                margin-bottom: 0.85rem;
                background: linear-gradient(145deg, rgba(255, 215, 0, 0.18), rgba(255, 255, 255, 0.02));
                border: 1px solid rgba(255, 215, 0, 0.18);
                color: #ffe38a;
                font-weight: 700;
                letter-spacing: 0.14rem;
                text-align: center;
            }
            .task-header {
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                align-items: flex-start;
                margin-bottom: 0.75rem;
            }
            .task-title {
                color: #ffd700;
                font-size: 1.05rem;
                font-weight: 700;
            }
            .footer-note {
                color: #c9bf95;
                text-align: center;
                padding: 0.5rem 0 1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )



def inject_autorefresh(interval_seconds: int) -> None:
    components.html(
        f"""
        <script>
            const interval = {interval_seconds * 1000};
            if (!window.__luxeRefreshScheduled) {{
                window.__luxeRefreshScheduled = true;
                setTimeout(function () {{
                    window.parent.location.reload();
                }}, interval);
            }}
        </script>
        """,
        height=0,
    )



def render_metric_card(title: str, value: str, delta: str, positive: bool = True) -> None:
    delta_class = "metric-delta-positive" if positive else "metric-delta-negative"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="{delta_class}">{delta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def format_health_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value).strftime("%H:%M:%S")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%H:%M:%S")
        except ValueError:
            return value
    return None



def task_title(task: dict[str, Any]) -> str:
    return str(
        task.get("title")
        or task.get("task_type")
        or task.get("name")
        or task.get("id")
        or "Pending task"
    )



def task_summary(task: dict[str, Any]) -> str:
    return str(
        task.get("description")
        or task.get("summary")
        or task.get("payload", {}).get("description")
        or "Awaiting executive review."
    )


st.set_page_config(
    page_title="Luxe Collective Command Center",
    page_icon="��",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_styles()
inject_autorefresh(REFRESH_INTERVAL)

st.session_state.last_refresh = time.time()

st.markdown(
    """
    <div class="luxe-shell">
        <div class="hero-card">
            <h1>Luxe Collective Command Center</h1>
            <p>Executive oversight for approvals, agent orchestration, design visibility, and sales intelligence.</p>
            <span class="status-pill">Live refresh every 5 seconds</span>
            <span class="status-pill">Boss approval workflow enabled</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## 👑 LUXE COLLECTIVE")
    st.caption("Luxury operations command console")
    st.markdown("### System Status")

    health = api_request("GET", "/health")
    if health:
        st.success("🟢 API Connected")
        last_updated = format_health_timestamp(health.get("timestamp") if isinstance(health, dict) else None)
        if last_updated:
            st.caption(f"Last updated: {last_updated}")
    else:
        st.error("🔴 API Disconnected")

    st.markdown("---")
    st.markdown("### Active Agents")
    for agent, status in AGENT_STATUS.items():
        st.markdown(
            f"""
            <div class="agent-row">
                <strong>{agent}</strong><br>
                <span class="muted">{status}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("🔄 Manual Refresh", use_container_width=True):
        st.rerun()

    st.caption(f"Auto-refresh interval: {REFRESH_INTERVAL} seconds")


tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📋 Screen 1: Approval Hub",
        "📺 Screen 2: Agent Activity",
        "🎨 Screen 3: Design Studio",
        "📊 Screen 4: Sales Intelligence",
    ]
)

with tab1:
    st.markdown("### Boss Agent Approval Hub")
    pending_tasks = api_request("GET", "/api/boss/pending")

    if pending_tasks is None:
        st.warning("Unable to fetch pending tasks. Check API connection.")
    elif not pending_tasks:
        st.info("✅ No pending tasks awaiting approval")
    else:
        st.write(f"**{len(pending_tasks)} tasks pending approval**")
        for task in pending_tasks:
            identifier = task.get("id", task_title(task))
            st.markdown(
                f"""
                <div class="activity-card">
                    <div class="task-header">
                        <div>
                            <div class="task-title">{task_title(task)}</div>
                            <div class="muted">{task_summary(task)}</div>
                        </div>
                        <span class="tag-pill">Task ID: {identifier}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("✅ Approve", key=f"approve_{identifier}", use_container_width=True):
                    result = api_request(
                        "POST",
                        f"/api/boss/review/{identifier}",
                        data={"decision": "APPROVED: Aligned with brand standards"},
                    )
                    if result is not None:
                        st.success("Task approved.")
                        time.sleep(0.4)
                        st.rerun()
                    else:
                        st.error("Approval failed")

            with col2:
                if st.button("❌ Reject", key=f"reject_{identifier}", use_container_width=True):
                    result = api_request(
                        "POST",
                        f"/api/boss/review/{identifier}",
                        data={"decision": "REJECT: Needs refinement in ancient symbolism"},
                    )
                    if result is not None:
                        st.error("Task rejected.")
                        time.sleep(0.4)
                        st.rerun()
                    else:
                        st.error("Rejection failed")

            with col3:
                feedback = task.get("boss_feedback")
                if feedback:
                    st.info(f"💡 Feedback: {feedback}")
                else:
                    st.caption("No prior boss feedback on this task.")

            with st.expander(f"Inspect task payload: {identifier}"):
                st.json(task)

with tab2:
    st.markdown("### Live Agent Activity Stream")
    current_time = datetime.now()

    for seconds_ago, agent, action in ACTIVITIES:
        activity_time = (current_time - timedelta(seconds=seconds_ago)).strftime("%H:%M:%S")
        st.markdown(
            f"""
            <div class="activity-card">
                <strong>{activity_time}</strong> · <span class="tag-pill">{agent}</span>
                <div style="margin-top:0.5rem;">{action}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.caption("💡 In production this stream should be replaced by a WebSocket or event API feed.")

with tab3:
    st.markdown("### Product Design Studio Feed")
    st.info("💡 Showing approved designs from Agents 02 (Logo) and 03 (Graphics)")

    cols = st.columns(3)
    for index, design in enumerate(APPROVED_DESIGNS):
        with cols[index % 3]:
            tags = "".join(f'<span class="tag-pill">{tag}</span>' for tag in design["tags"])
            st.markdown(
                f"""
                <div class="design-card">
                    <div class="preview-box">{design['preview']}</div>
                    <h4>{design['name']}</h4>
                    <p class="muted">{design['description']}</p>
                    <div>{tags}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    stat1, stat2, stat3, stat4 = st.columns(4)
    with stat1:
        st.metric("Approved Today", "12", "+3")
    with stat2:
        st.metric("Pending Review", "5", "-2")
    with stat3:
        st.metric("In Production", "8", "+1")
    with stat4:
        st.metric("This Week", "67", "+15%")

with tab4:
    st.markdown("### Sales & Performance Intelligence")

    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_metric_card("Revenue Today", format_currency(24_850), format_percent(12.4))
    with metric_cols[1]:
        render_metric_card("Orders Today", "420", format_percent(8.1))
    with metric_cols[2]:
        render_metric_card("Conversion Rate", "4.9%", format_percent(1.2))
    with metric_cols[3]:
        render_metric_card("Ad Spend Efficiency", "5.8x", format_percent(-0.6), positive=False)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("Daily Revenue Trend")
        dates = [(datetime.now() - timedelta(days=i)).strftime("%m/%d") for i in range(6, -1, -1)]
        revenue = [18200, 19500, 21000, 17800, 22500, 23800, 24850]

        revenue_fig = go.Figure()
        revenue_fig.add_trace(
            go.Scatter(
                x=dates,
                y=revenue,
                mode="lines+markers",
                line={"color": "#ffd700", "width": 3},
                marker={"size": 8, "color": "#ffd700"},
                fill="tozeroy",
                fillcolor="rgba(255, 215, 0, 0.1)",
            )
        )
        revenue_fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            height=320,
        )
        revenue_fig.update_xaxes(showgrid=False, zeroline=False)
        revenue_fig.update_yaxes(showgrid=False, zeroline=False, tickprefix="$")
        st.plotly_chart(revenue_fig, use_container_width=True)

    with chart_col2:
        st.subheader("Sales by Category")
        category_fig = go.Figure(
            data=[
                go.Pie(
                    labels=["Streetwear", "Formal", "Accessories", "Footwear", "Lingerie"],
                    values=[45, 25, 15, 10, 5],
                    hole=0.4,
                    marker_colors=["#ffd700", "#88ccff", "#00ff88", "#ff4444", "#ff8800"],
                )
            ]
        )
        category_fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            height=320,
        )
        st.plotly_chart(category_fig, use_container_width=True)

    st.subheader("Top Performing Products")
    st.dataframe(
        pd.DataFrame(TOP_PRODUCTS),
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Product": st.column_config.TextColumn("Product", width="medium"),
            "SKU": st.column_config.TextColumn("SKU", width="small"),
            "Units": st.column_config.NumberColumn("Units Sold", width="small"),
            "Revenue": st.column_config.TextColumn("Revenue", width="small"),
            "Margin": st.column_config.TextColumn("Margin", width="small"),
        },
        hide_index=True,
        use_container_width=True,
    )

    perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
    with perf_col1:
        st.metric("Return Rate", "2.1%", "-0.3%")
    with perf_col2:
        st.metric("Avg. Order Value", "$59.20", "+$4.80")
    with perf_col3:
        st.metric("Customer Acquisition Cost", "$12.40", "-$1.20")
    with perf_col4:
        st.metric("Inventory Turnover", "4.2x", "+0.5x")

    st.caption("💡 Replace this mock data with admin analytics endpoints when backend reporting is ready.")

st.markdown("---")
st.markdown(
    "<div class='footer-note'>LUXE Collective Command Center · Approval workflow live · Simulated screens ready for backend integration</div>",
    unsafe_allow_html=True,
)
