"""
Luxe Collective – Real-Time Dashboard
Four screens showing the live multi-agent workflow.

Run locally:  streamlit run dashboard.py
Via Docker:   Started automatically by docker-compose
"""
import json
import os
import time

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://api:8000")

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Luxe Collective – Boss Agent Dashboard",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    .agent-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 4px;
    }
    .status-pending    { background:#FFF3CD; color:#856404; }
    .status-boss_review{ background:#CCE5FF; color:#004085; }
    .status-approved   { background:#D4EDDA; color:#155724; }
    .status-rejected   { background:#F8D7DA; color:#721C24; }
    .status-logo_design{ background:#E2D9F3; color:#432874; }
    .status-graphic_design{ background:#D1ECF1; color:#0C5460; }
    .status-print_sourcing{ background:#FDE8D8; color:#7D3000; }
    .status-completed  { background:#1E7E34; color:#FFFFFF; }
    .status-failed     { background:#721C24; color:#FFFFFF; }
    </style>
    """,
    unsafe_allow_html=True,
)

STATUS_EMOJI = {
    "pending": "⏳",
    "boss_review": "🔍",
    "approved": "✅",
    "rejected": "❌",
    "logo_design": "🎨",
    "graphic_design": "🖼️",
    "print_sourcing": "🏭",
    "completed": "🎉",
    "failed": "💥",
}

AGENT_COLOUR = {
    "agent_01": "#4A90D9",
    "agent_02": "#9B59B6",
    "agent_03": "#E67E22",
    "agent_05": "#27AE60",
}

# ── API helpers ───────────────────────────────────────────────────────────────


def api_get(path: str):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"error": str(exc)}


def api_post(path: str, data: dict):
    try:
        r = requests.post(f"{API_BASE}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"error": str(exc)}


def api_delete(path: str):
    try:
        r = requests.delete(f"{API_BASE}{path}", timeout=5)
        return r.status_code
    except Exception:
        return 500


def badge(status: str) -> str:
    emoji = STATUS_EMOJI.get(status, "❓")
    return f'<span class="agent-badge status-{status}">{emoji} {status.replace("_", " ").title()}</span>'


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image(
        "https://via.placeholder.com/200x60/1A1A2E/E8D5B7?text=LUXE+COLLECTIVE",
        use_column_width=True,
    )
    st.markdown("### 👑 Boss Agent Dashboard")
    st.markdown("---")
    screen = st.radio(
        "Navigate",
        ["📋 Submit Task", "📊 Task Queue", "🔍 Task Detail", "🏭 Print Sourcing"],
        label_visibility="collapsed",
    )
    st.markdown("---")

    # Health check
    health = api_get("/health")
    if "error" in health:
        st.error(f"⚠️ API Offline\n{health['error']}")
    else:
        st.success("✅ API Connected")

    st.markdown("---")
    auto_refresh = st.checkbox("Auto-refresh (5 s)", value=True)
    if st.button("🔄 Refresh Now"):
        st.rerun()

    use_mock = os.getenv("USE_MOCK_AI", "true").lower() == "true"
    mode_label = "🎭 Mock AI Mode" if use_mock else "🤖 Real AI Mode"
    st.info(mode_label)


# ── Screen 1: Submit Task ─────────────────────────────────────────────────────

if screen == "📋 Submit Task":
    st.title("📋 Submit New Design Task")
    st.markdown(
        "Fill in the creative brief below. The **Boss Agent** will review it immediately, "
        "then pass it through the full design pipeline."
    )

    with st.form("task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Task Title *", placeholder="e.g. Summer Drop 2025 – Core Tee")
            brand_name = st.text_input("Brand Name *", placeholder="e.g. NOCTURNE")
            product_type = st.selectbox(
                "Product Type *",
                ["T-Shirt", "Hoodie", "Sweatshirt", "Cap", "Polo", "Tote Bag", "Other"],
            )
        with col2:
            quantity = st.number_input("Quantity (units) *", min_value=25, max_value=10000, value=100, step=25)
            budget_usd = st.number_input("Budget (USD) *", min_value=100, max_value=50000, value=500, step=50)

        style_description = st.text_area(
            "Style Description *",
            placeholder=(
                "Describe the aesthetic, mood, target audience, and any visual references.\n"
                "Example: Minimalist streetwear inspired by brutalist architecture. "
                "Target: 18–28 urban creatives. Tone-on-tone palette with a single bold accent. "
                "References: Rick Owens, Cactus Plant Flea Market."
            ),
            height=140,
        )

        submitted = st.form_submit_button("🚀 Submit to Boss Agent", use_container_width=True)

        if submitted:
            if not all([title, brand_name, style_description]):
                st.error("Please fill in all required fields.")
            else:
                with st.spinner("Submitting to pipeline…"):
                    result = api_post(
                        "/api/tasks/",
                        {
                            "title": title,
                            "brand_name": brand_name,
                            "product_type": product_type,
                            "style_description": style_description,
                            "quantity": int(quantity),
                            "budget_usd": int(budget_usd),
                        },
                    )
                if "error" in result:
                    st.error(f"Submission failed: {result['error']}")
                else:
                    st.success(
                        f"✅ Task **#{result['id']}** submitted! "
                        "Switch to **Task Queue** to watch the agents work."
                    )
                    st.json(result)

    st.markdown("---")
    st.markdown(
        "**Pipeline Flow:** Submit → 🔍 Boss Review → 🎨 Logo Design → 🖼️ Graphic Design → 🏭 Print Sourcing → 🎉 Complete"
    )


# ── Screen 2: Task Queue ──────────────────────────────────────────────────────

elif screen == "📊 Task Queue":
    st.title("📊 Task Queue")

    tasks = api_get("/api/tasks/")
    if "error" in tasks:
        st.error(f"Could not load tasks: {tasks['error']}")
    elif not tasks:
        st.info("No tasks yet. Go to **Submit Task** to create your first one.")
    else:
        # Summary metrics
        statuses = [t["status"] for t in tasks]
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Tasks", len(tasks))
        col2.metric("🎉 Completed", statuses.count("completed"))
        col3.metric("⚙️ In Progress", sum(1 for s in statuses if s not in ("completed", "rejected", "failed", "pending")))
        col4.metric("❌ Rejected", statuses.count("rejected"))
        col5.metric("💥 Failed", statuses.count("failed"))

        st.markdown("---")

        for t in tasks:
            with st.container():
                col_a, col_b, col_c = st.columns([5, 2, 1])
                with col_a:
                    st.markdown(
                        f"**#{t['id']}** {t['title']}  \n"
                        f"*{t['brand_name']}* · {t['product_type']} · {t['quantity']} units · ${t['budget_usd']}",
                        unsafe_allow_html=False,
                    )
                with col_b:
                    st.markdown(badge(t["status"]), unsafe_allow_html=True)
                with col_c:
                    if st.button("🔍", key=f"view_{t['id']}", help="View detail"):
                        st.session_state["selected_task_id"] = t["id"]
                        st.rerun()
                st.divider()

    if auto_refresh:
        time.sleep(5)
        st.rerun()


# ── Screen 3: Task Detail ─────────────────────────────────────────────────────

elif screen == "🔍 Task Detail":
    st.title("🔍 Task Detail")

    # Task selector
    tasks = api_get("/api/tasks/")
    if "error" in tasks or not tasks:
        st.info("No tasks available. Submit one first.")
    else:
        task_options = {f"#{t['id']} – {t['title']} ({t['status']})": t["id"] for t in tasks}
        default_idx = 0
        if "selected_task_id" in st.session_state:
            ids = list(task_options.values())
            if st.session_state["selected_task_id"] in ids:
                default_idx = ids.index(st.session_state["selected_task_id"])

        selected_label = st.selectbox("Select Task", list(task_options.keys()), index=default_idx)
        task_id = task_options[selected_label]

        task = api_get(f"/api/tasks/{task_id}")
        if "error" in task:
            st.error(f"Could not load task: {task['error']}")
        else:
            # Header
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"#{task['id']} – {task['title']}")
                st.caption(f"{task['brand_name']} · {task['product_type']} · {task['quantity']} units · ${task['budget_usd']}")
            with col2:
                st.markdown(badge(task["status"]), unsafe_allow_html=True)
                if st.button("🗑️ Delete Task", type="secondary"):
                    code = api_delete(f"/api/tasks/{task_id}")
                    if code == 204:
                        st.success("Task deleted.")
                        st.rerun()
                    else:
                        st.error("Could not delete task.")

            st.markdown(f"**Brief:** {task['style_description']}")
            st.markdown("---")

            # Pipeline progress
            pipeline_steps = [
                ("agent_01", "Agent 01 – Boss Agent", "🔍"),
                ("agent_02", "Agent 02 – Logo Designer", "🎨"),
                ("agent_03", "Agent 03 – Graphic Designer", "🖼️"),
                ("agent_05", "Agent 05 – Print Sourcing", "🏭"),
            ]
            results_by_agent = {r["agent_id"]: r for r in task.get("results", [])}

            st.markdown("### 🤖 Agent Pipeline")
            cols = st.columns(4)
            for idx, (agent_id, agent_name, emoji) in enumerate(pipeline_steps):
                with cols[idx]:
                    if agent_id in results_by_agent:
                        res = results_by_agent[agent_id]
                        colour = "green" if res["status"] == "success" else "red"
                        st.markdown(
                            f":{colour}[{emoji} **{agent_name}**]  \n✅ Done"
                        )
                    elif task["status"] in ("completed", "rejected", "failed"):
                        st.markdown(f"⬜ {emoji} **{agent_name}**  \n⏭️ Skipped")
                    else:
                        st.markdown(f"⏳ {emoji} **{agent_name}**  \n🔄 Pending")

            st.markdown("---")

            # Agent results
            if task.get("results"):
                st.markdown("### 📄 Agent Results")
                for res in task["results"]:
                    colour = AGENT_COLOUR.get(res["agent_id"], "#888")
                    with st.expander(
                        f"{res['agent_name']}  ·  {res['result_type'].replace('_', ' ').title()}  ·  {res['status'].upper()}",
                        expanded=(res["agent_id"] == "agent_01"),
                    ):
                        try:
                            parsed = json.loads(res["content"])
                            if res["result_type"] == "approval":
                                verdict = parsed.get("status", "")
                                feedback = parsed.get("feedback", "")
                                if verdict == "approved":
                                    st.success(feedback)
                                else:
                                    st.error(feedback)

                            elif res["result_type"] == "logo_concept":
                                c1, c2 = st.columns([2, 1])
                                with c1:
                                    st.markdown(f"**Concept:** {parsed.get('concept_name')}")
                                    st.markdown(f"**Symbol:** {parsed.get('primary_symbol')}")
                                    st.markdown(f"**Typography:** {parsed.get('typography')}")
                                    st.markdown(f"**Style Notes:** {parsed.get('style_notes')}")
                                    st.markdown(f"**Usage:** {parsed.get('usage')}")
                                    st.markdown(f"**Rationale:** {parsed.get('rationale')}")
                                with c2:
                                    colours = parsed.get("color_palette", [])
                                    names = parsed.get("color_names", [])
                                    for hex_c, name in zip(colours, names):
                                        st.markdown(
                                            f'<div style="background:{hex_c};padding:8px 12px;'
                                            f'border-radius:6px;color:{"#fff" if hex_c < "#888888" else "#000"};'
                                            f'margin-bottom:4px;font-size:0.8rem;">'
                                            f'{name}<br><code>{hex_c}</code></div>',
                                            unsafe_allow_html=True,
                                        )

                            elif res["result_type"] == "graphic":
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.markdown(f"**Graphic:** {parsed.get('graphic_name')}")
                                    st.markdown(f"**Placement:** {parsed.get('placement')}")
                                    dims = parsed.get("dimensions_cm", {})
                                    st.markdown(f"**Size:** {dims.get('width')} × {dims.get('height')} cm")
                                    st.markdown(f"**Technique:** {parsed.get('print_technique')}")
                                    st.markdown(f"**Colour Seps:** {parsed.get('colour_separations')}")
                                    st.markdown(f"**File Req:** {parsed.get('file_requirements')}")
                                with c2:
                                    est = parsed.get("estimated_print_cost_per_unit_usd")
                                    if est:
                                        st.metric("Est. Print Cost/Unit", f"${est:.2f}")
                                    st.markdown(f"**Garment Notes:** {parsed.get('garment_notes')}")
                                    st.markdown(f"♻️ {parsed.get('sustainability_flag')}")
                                    layers = parsed.get("layers", [])
                                    if layers:
                                        st.markdown("**Layers:**")
                                        for layer in layers:
                                            st.markdown(f"- Layer {layer.get('layer')}: {layer.get('description')}")

                            elif res["result_type"] == "print_quote":
                                rec = parsed.get("recommended_vendor") or {}
                                if rec:
                                    st.success(
                                        f"**Recommended:** {rec.get('vendor_name')}  \n"
                                        f"{parsed.get('recommendation_rationale', '')}"
                                    )
                                quotes = parsed.get("quotes", [])
                                if quotes:
                                    import pandas as pd
                                    df = pd.DataFrame(
                                        [
                                            {
                                                "Vendor": q["vendor_name"],
                                                "Location": q["location"],
                                                "Unit Cost ($)": q["unit_cost_usd"],
                                                "Total ($)": q["total_cost_usd"],
                                                "Days": q["turnaround_days"],
                                                "Rating": q["quality_rating"],
                                                "Eco ✓": "✅" if q["sustainability_certified"] else "—",
                                                "In Budget": "✅" if q["within_budget"] else "⚠️",
                                                "Score": q.get("score", 0),
                                            }
                                            for q in quotes
                                        ]
                                    ).sort_values("Score", ascending=False)
                                    st.dataframe(df, use_container_width=True, hide_index=True)

                            else:
                                st.json(parsed)
                        except json.JSONDecodeError:
                            st.text(res["content"])

            # Activity log
            if task.get("logs"):
                st.markdown("---")
                st.markdown("### 📝 Activity Log")
                for log in reversed(task["logs"]):
                    ts = log["created_at"][:19].replace("T", " ")
                    st.markdown(
                        f"`{ts}` **{log.get('agent', 'System')}** › {log.get('action', '')} — {log.get('message', '')}"
                    )

        if auto_refresh and task.get("status") not in ("completed", "rejected", "failed"):
            time.sleep(3)
            st.rerun()


# ── Screen 4: Print Sourcing ──────────────────────────────────────────────────

elif screen == "🏭 Print Sourcing":
    st.title("🏭 Print Sourcing – Vendor Comparison")

    tasks = api_get("/api/tasks/")
    completed = [t for t in (tasks if isinstance(tasks, list) else []) if t["status"] == "completed"]

    if not completed:
        st.info("No completed tasks yet. Tasks must complete the full pipeline to see vendor quotes here.")
    else:
        task_options = {f"#{t['id']} – {t['title']}": t["id"] for t in completed}
        selected_label = st.selectbox("Select completed task", list(task_options.keys()))
        task_id = task_options[selected_label]
        task = api_get(f"/api/tasks/{task_id}")

        if "error" not in task:
            print_result_raw = next(
                (r["content"] for r in task.get("results", []) if r["result_type"] == "print_quote"),
                None,
            )
            if print_result_raw:
                data = json.loads(print_result_raw)
                rec = data.get("recommended_vendor") or {}
                quotes = data.get("quotes", [])

                st.markdown(f"**Brand:** {task['brand_name']}  ·  **Product:** {task['product_type']}  ·  **Qty:** {task['quantity']}  ·  **Budget:** ${task['budget_usd']}")
                st.markdown("---")

                if rec:
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("🏆 Best Vendor", rec.get("vendor_name", "—"))
                    col2.metric("💰 Total Cost", f"${rec.get('total_cost_usd', 0):,.2f}")
                    col3.metric("📅 Turnaround", f"{rec.get('turnaround_days', '?')} days")
                    col4.metric("⭐ Rating", f"{rec.get('quality_rating', '?')}/5")
                    st.success(f"💡 {data.get('recommendation_rationale', '')}")
                    st.markdown("---")

                if quotes:
                    import pandas as pd
                    import plotly.express as px

                    df = pd.DataFrame(
                        [
                            {
                                "Vendor": q["vendor_name"],
                                "Location": q["location"],
                                "Unit Cost ($)": q["unit_cost_usd"],
                                "Total Cost ($)": q["total_cost_usd"],
                                "Turnaround (days)": q["turnaround_days"],
                                "Quality Rating": q["quality_rating"],
                                "Eco Certified": "Yes" if q["sustainability_certified"] else "No",
                                "Within Budget": "Yes" if q["within_budget"] else "No",
                                "Score": q.get("score", 0),
                            }
                            for q in quotes
                        ]
                    ).sort_values("Score", ascending=False)

                    st.subheader("📊 Vendor Comparison")
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    # Bar chart: total cost by vendor
                    fig = px.bar(
                        df,
                        x="Vendor",
                        y="Total Cost ($)",
                        color="Eco Certified",
                        color_discrete_map={"Yes": "#27AE60", "No": "#E74C3C"},
                        title="Total Cost by Vendor",
                        text="Total Cost ($)",
                    )
                    fig.add_hline(y=task["budget_usd"], line_dash="dash", line_color="orange", annotation_text="Budget")
                    st.plotly_chart(fig, use_container_width=True)

                    # Scatter: quality vs cost
                    fig2 = px.scatter(
                        df,
                        x="Total Cost ($)",
                        y="Quality Rating",
                        size="Turnaround (days)",
                        color="Eco Certified",
                        hover_name="Vendor",
                        color_discrete_map={"Yes": "#27AE60", "No": "#E74C3C"},
                        title="Quality vs Cost (bubble size = turnaround days)",
                    )
                    st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("Print sourcing data not available for this task.")
