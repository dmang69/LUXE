"""
LUXE COLLECTIVE - Boss Agent & Specialized Agents
AI-Powered Brand Management with Streamlit Dashboard
"""

import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ─── Task Status & Priority ───────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class AgentTask:
    task_id: str
    agent_id: str
    agent_name: str
    task_type: str
    description: str
    payload: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    feedback: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


@dataclass
class DesignVariation:
    variation_id: str
    culture: str
    product_line: str
    symbol_name: str
    description: str
    color_palette: List[str]
    design_elements: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)


# ─── Boss Agent ───────────────────────────────────────────────────────────────

class BossAgent:
    """
    Central authority agent for LUXE COLLECTIVE.
    All specialized agents must route tasks through BossAgent for approval.
    """

    def __init__(self):
        self.agent_id = "boss-agent-01"
        self.name = "Boss Agent"
        self.pending_tasks: List[AgentTask] = []
        self.approved_tasks: List[AgentTask] = []
        self.rejected_tasks: List[AgentTask] = []
        self.agent_registry: Dict[str, Any] = {}

        # Brand guardrails
        self.brand_guidelines = {
            "cultures": ["Egyptian", "Mesopotamian", "Mayan", "Norse", "Celtic", "Greek"],
            "forbidden_keywords": ["generic", "basic", "mainstream"],
            "required_elements": ["ancient symbolism", "luxury aesthetic"],
            "max_variations_per_request": 10,
        }

    def register_agent(self, agent) -> None:
        self.agent_registry[agent.agent_id] = agent

    async def submit_task(self, task: AgentTask) -> str:
        """Receive a task submission from a specialized agent."""
        self.pending_tasks.append(task)
        print(f"📥 Boss Agent received task [{task.task_id}] from {task.agent_name}")
        return task.task_id

    async def review_task(self, task_id: str) -> AgentTask:
        """Review and auto-evaluate a pending task against brand guidelines."""
        task = next((t for t in self.pending_tasks if t.task_id == task_id), None)
        if not task:
            raise ValueError(f"Task {task_id} not found in pending queue")

        approved, feedback = self._evaluate_task(task)
        task.status = TaskStatus.APPROVED if approved else TaskStatus.REJECTED
        task.feedback = feedback
        task.reviewed_at = datetime.utcnow()

        self.pending_tasks.remove(task)
        if approved:
            self.approved_tasks.append(task)
            print(f"✅ Task [{task_id}] APPROVED: {feedback}")
        else:
            self.rejected_tasks.append(task)
            print(f"❌ Task [{task_id}] REJECTED: {feedback}")

        return task

    def _evaluate_task(self, task: AgentTask):
        """Evaluate a task payload against brand guidelines."""
        payload = task.payload

        # Check forbidden keywords in description
        desc_lower = task.description.lower()
        for kw in self.brand_guidelines["forbidden_keywords"]:
            if kw in desc_lower:
                return False, f"Description contains forbidden keyword: '{kw}'"

        # Logo design validation
        if task.task_type == "logo_design":
            culture = payload.get("culture", "")
            if culture not in self.brand_guidelines["cultures"]:
                return False, f"Culture '{culture}' is not in approved list"
            num = payload.get("num_variations", 1)
            if num > self.brand_guidelines["max_variations_per_request"]:
                return False, f"Requested {num} variations exceeds maximum of {self.brand_guidelines['max_variations_per_request']}"

        # Graphic design validation
        if task.task_type == "graphic_design":
            required = self.brand_guidelines["required_elements"]
            design_notes = payload.get("design_notes", "").lower()
            missing = [el for el in required if el not in design_notes]
            if missing:
                return False, f"Design is missing required brand elements: {missing}"

        return True, "Meets all brand guidelines."

    def manual_approve(self, task_id: str, feedback: str = "Manually approved.") -> bool:
        task = next((t for t in self.pending_tasks if t.task_id == task_id), None)
        if not task:
            return False
        task.status = TaskStatus.APPROVED
        task.feedback = feedback
        task.reviewed_at = datetime.utcnow()
        self.pending_tasks.remove(task)
        self.approved_tasks.append(task)
        return True

    def manual_reject(self, task_id: str, feedback: str = "Manually rejected.") -> bool:
        task = next((t for t in self.pending_tasks if t.task_id == task_id), None)
        if not task:
            return False
        task.status = TaskStatus.REJECTED
        task.feedback = feedback
        task.reviewed_at = datetime.utcnow()
        self.pending_tasks.remove(task)
        self.rejected_tasks.append(task)
        return True

    def get_stats(self) -> Dict[str, int]:
        return {
            "pending": len(self.pending_tasks),
            "approved": len(self.approved_tasks),
            "rejected": len(self.rejected_tasks),
            "total": len(self.pending_tasks) + len(self.approved_tasks) + len(self.rejected_tasks),
        }


# ─── Base Specialized Agent ───────────────────────────────────────────────────

class SpecializedAgent:
    def __init__(self, agent_id: str, name: str, specialty: str):
        self.agent_id = agent_id
        self.name = name
        self.specialty = specialty
        self.boss_agent: Optional[BossAgent] = None
        self.activity_log: List[str] = []

    def _log(self, message: str) -> None:
        entry = f"[{datetime.utcnow().strftime('%H:%M:%S')}] {self.name}: {message}"
        self.activity_log.append(entry)
        print(entry)

    async def submit_task(self, task_type: str, description: str, payload: Dict[str, Any],
                          priority: TaskPriority = TaskPriority.MEDIUM) -> AgentTask:
        if not self.boss_agent:
            raise RuntimeError("Agent has no Boss Agent assigned")

        task = AgentTask(
            task_id=str(uuid.uuid4())[:8].upper(),
            agent_id=self.agent_id,
            agent_name=self.name,
            task_type=task_type,
            description=description,
            payload=payload,
            priority=priority,
        )
        await self.boss_agent.submit_task(task)
        self._log(f"Submitted task [{task.task_id}]: {description}")
        return task


# ─── Agent 02: Ancient Symbol Logo Designer ───────────────────────────────────

class AncientSymbolLogoDesigner(SpecializedAgent):
    def __init__(self):
        super().__init__(
            agent_id="agent-02-logo",
            name="Ancient Symbol Logo Designer",
            specialty="Logo design using ancient cultural symbolism",
        )

        self.symbol_library = {
            "Egyptian": ["Ankh", "Eye of Ra", "Scarab", "Djed Pillar", "Was Scepter"],
            "Mesopotamian": ["Star of Ishtar", "Lamassu", "Tree of Life", "Sun Disk"],
            "Mayan": ["Quetzalcoatl", "Hunab Ku", "Kin Glyph", "Tzolkin"],
            "Norse": ["Valknut", "Vegvisir", "Yggdrasil", "Mjolnir"],
            "Celtic": ["Triquetra", "Celtic Knot", "Spiral", "Ogham"],
            "Greek": ["Meander", "Labyrinth", "Olympian Wreath", "Ouroboros"],
        }

    async def generate_logo_variations(
        self,
        culture: str,
        product_line: str,
        num_variations: int = 3,
    ) -> List[DesignVariation]:
        self._log(f"Generating {num_variations} logo variation(s) for {culture} × {product_line}")

        symbols = self.symbol_library.get(culture, ["Universal Symbol"])
        variations: List[DesignVariation] = []

        for i in range(num_variations):
            symbol = symbols[i % len(symbols)]
            variation = DesignVariation(
                variation_id=f"LOGO-{culture[:3].upper()}-{i + 1:02d}",
                culture=culture,
                product_line=product_line,
                symbol_name=symbol,
                description=f"{symbol} integrated into luxury streetwear monogram for {product_line}",
                color_palette=self._get_color_palette(culture),
                design_elements=[symbol, "Gold leaf accent", "Minimal geometry", "Premium typography"],
            )
            variations.append(variation)

        # Submit to Boss Agent for approval
        task = await self.submit_task(
            task_type="logo_design",
            description=f"Logo variations using {culture} symbolism for {product_line}",
            payload={
                "culture": culture,
                "product_line": product_line,
                "num_variations": num_variations,
                "variations": [v.__dict__ for v in variations],
            },
            priority=TaskPriority.HIGH,
        )
        return variations

    @staticmethod
    def _get_color_palette(culture: str) -> List[str]:
        palettes = {
            "Egyptian": ["#C9A84C", "#2C1810", "#F5F0E8", "#8B1A1A"],
            "Mesopotamian": ["#4A3728", "#C4A35A", "#2B4C7E", "#F0E6D3"],
            "Mayan": ["#006400", "#8B0000", "#FFD700", "#1C1C1C"],
            "Norse": ["#2C3E6B", "#C0C0C0", "#1A1A1A", "#B8860B"],
            "Celtic": ["#228B22", "#800000", "#C0C0C0", "#F5DEB3"],
            "Greek": ["#FFFFFF", "#1C2B6E", "#C9A84C", "#2C2C2C"],
        }
        return palettes.get(culture, ["#000000", "#FFFFFF", "#C9A84C"])


# ─── Agent 03: Graphic Design Specialist ──────────────────────────────────────

class GraphicDesignSpecialist(SpecializedAgent):
    def __init__(self):
        super().__init__(
            agent_id="agent-03-graphics",
            name="Graphic Design Specialist",
            specialty="Premium graphic design for luxury fashion",
        )

    async def create_collection_artwork(
        self,
        collection_name: str,
        season: str,
        design_notes: str,
    ) -> AgentTask:
        self._log(f"Creating artwork for collection: {collection_name} ({season})")

        return await self.submit_task(
            task_type="graphic_design",
            description=f"Collection artwork for {collection_name} — {season}",
            payload={
                "collection_name": collection_name,
                "season": season,
                "design_notes": design_notes,
                "deliverables": ["hero image", "lookbook spread", "social media assets"],
            },
            priority=TaskPriority.HIGH,
        )


# ─── Streamlit Dashboard ──────────────────────────────────────────────────────

def run_dashboard():
    st.set_page_config(
        page_title="LUXE COLLECTIVE Command Center",
        page_icon="👑",
        layout="wide",
    )

    st.title("👑 LUXE COLLECTIVE Command Center")
    st.caption("Boss Agent — Real-Time Brand Intelligence Dashboard")

    # Initialize Boss Agent in session state
    if "boss" not in st.session_state:
        boss = BossAgent()

        logo_agent = AncientSymbolLogoDesigner()
        gfx_agent = GraphicDesignSpecialist()
        logo_agent.boss_agent = boss
        gfx_agent.boss_agent = boss
        boss.register_agent(logo_agent)
        boss.register_agent(gfx_agent)
        st.session_state.boss = boss
        st.session_state.logo_agent = logo_agent
        st.session_state.gfx_agent = gfx_agent

    boss: BossAgent = st.session_state.boss

    # ── Sidebar: Stats ────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("📊 System Overview")
        stats = boss.get_stats()
        st.metric("Total Tasks", stats["total"])
        st.metric("Pending Review", stats["pending"])
        st.metric("Approved", stats["approved"])
        st.metric("Rejected", stats["rejected"])

        st.divider()
        st.header("🤖 Submit Demo Task")
        culture = st.selectbox("Culture", boss.brand_guidelines["cultures"])
        product_line = st.text_input("Product Line", value="Luxury Streetwear")
        num_var = st.slider("Variations", 1, 5, 2)

        if st.button("🎨 Generate Logo Variations"):
            asyncio.run(
                st.session_state.logo_agent.generate_logo_variations(
                    culture=culture,
                    product_line=product_line,
                    num_variations=num_var,
                )
            )
            st.success("Task submitted to Boss Agent!")
            st.rerun()

    # ── Tab Layout ────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["🔔 Approval Hub", "🤖 Agent Activity", "🎨 Design Gallery"])

    # Tab 1: Approval Hub
    with tab1:
        st.subheader("Pending Tasks")
        if not boss.pending_tasks:
            st.info("No pending tasks. Use the sidebar to submit a task.")
        for task in boss.pending_tasks:
            with st.expander(f"[{task.task_id}] {task.description} — {task.priority.upper()}"):
                st.json(task.payload)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve", key=f"approve_{task.task_id}"):
                        boss.manual_approve(task.task_id)
                        st.rerun()
                with col2:
                    if st.button("❌ Reject", key=f"reject_{task.task_id}"):
                        boss.manual_reject(task.task_id, feedback="Rejected by human overseer.")
                        st.rerun()

        st.divider()
        st.subheader("Recently Reviewed")
        reviewed = boss.approved_tasks + boss.rejected_tasks
        reviewed.sort(key=lambda t: t.reviewed_at or datetime.min, reverse=True)
        for task in reviewed[:10]:
            icon = "✅" if task.status == TaskStatus.APPROVED else "❌"
            st.write(f"{icon} **[{task.task_id}]** {task.description} — *{task.feedback}*")

    # Tab 2: Agent Activity
    with tab2:
        st.subheader("Agent Activity Log")
        for agent in [st.session_state.logo_agent, st.session_state.gfx_agent]:
            with st.expander(f"🤖 {agent.name}"):
                if agent.activity_log:
                    for entry in reversed(agent.activity_log):
                        st.text(entry)
                else:
                    st.caption("No activity yet.")

    # Tab 3: Design Gallery
    with tab3:
        st.subheader("Approved Design Assets")
        approved_logos = [
            t for t in boss.approved_tasks if t.task_type == "logo_design"
        ]
        if not approved_logos:
            st.info("No approved designs yet. Approve tasks in the Approval Hub.")
        for task in approved_logos:
            st.write(f"**{task.description}**")
            variations = task.payload.get("variations", [])
            cols = st.columns(min(len(variations), 3) or 1)
            for i, var in enumerate(variations):
                with cols[i % 3]:
                    st.markdown(f"**{var['symbol_name']}**")
                    st.caption(var["description"])
                    palette = var.get("color_palette", [])
                    if palette:
                        swatches = " ".join(
                            f'<span style="background:{c};width:20px;height:20px;display:inline-block;border-radius:3px;margin:2px"></span>'
                            for c in palette
                        )
                        st.markdown(swatches, unsafe_allow_html=True)


# ─── Main Entry Point ─────────────────────────────────────────────────────────

async def main():
    boss = BossAgent()

    agents = [
        AncientSymbolLogoDesigner(),
        GraphicDesignSpecialist(),
        # Add Agents 04-10 here
    ]

    for agent in agents:
        agent.boss_agent = boss
        boss.register_agent(agent)

    # Demo: generate logo variations and auto-review
    logo_agent = agents[0]
    await logo_agent.generate_logo_variations(
        culture="Egyptian",
        product_line="Luxury Streetwear",
        num_variations=2,
    )
    for task in list(boss.pending_tasks):
        await boss.review_task(task.task_id)

    print("\n🚀 LUXE COLLECTIVE Command Center")
    print("📡 Boss Agent is online")
    print("🌐 Dashboard: streamlit run boss_agent.py --server.port 8501")


if __name__ == "__main__":
    # When invoked by Streamlit, run the dashboard; otherwise run async demo
    try:
        import streamlit.runtime.scriptrunner as sr

        if sr.get_script_run_ctx():
            run_dashboard()
        else:
            asyncio.run(main())
    except ImportError:
        asyncio.run(main())
