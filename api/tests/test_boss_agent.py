"""
Tests for the Boss Agent mock review logic.
These run without a database or network – the agent module is self-contained.
"""
import os
import sys

# Allow importing from the api/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Force mock mode so no real AI calls are made
os.environ["USE_MOCK_AI"] = "true"
# Provide a dummy DATABASE_URL to avoid import-time errors from database.py
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from agents import boss_agent  # noqa: E402


VALID_BRIEF = {
    "title": "Summer Drop 2025",
    "brand_name": "NOCTURNE",
    "product_type": "T-Shirt",
    "style_description": "Minimalist streetwear with bold typography",
    "quantity": 100,
    "budget_usd": 500,
}


class TestBossAgentMock:
    def test_approves_valid_brief(self):
        result = boss_agent.run(VALID_BRIEF)
        assert result["status"] == "approved"
        assert "Approved" in result["feedback"]

    def test_rejects_brief_below_20_chars(self):
        brief = {**VALID_BRIEF, "style_description": "Too short"}
        result = boss_agent.run(brief)
        assert result["status"] == "rejected"
        assert "20" in result["feedback"]

    def test_rejects_exactly_19_chars(self):
        brief = {**VALID_BRIEF, "style_description": "A" * 19}
        result = boss_agent.run(brief)
        assert result["status"] == "rejected"

    def test_approves_exactly_20_chars(self):
        brief = {**VALID_BRIEF, "style_description": "A" * 20}
        result = boss_agent.run(brief)
        assert result["status"] == "approved"

    def test_rejects_insufficient_budget(self):
        # budget < qty * 2: 100 units, budget $150 → below $200 minimum
        brief = {**VALID_BRIEF, "quantity": 100, "budget_usd": 150}
        result = boss_agent.run(brief)
        assert result["status"] == "rejected"
        assert "Budget" in result["feedback"] or "budget" in result["feedback"].lower()

    def test_approves_budget_at_minimum(self):
        # budget == qty * 2: exactly $200 for 100 units
        brief = {**VALID_BRIEF, "quantity": 100, "budget_usd": 200}
        result = boss_agent.run(brief)
        assert result["status"] == "approved"

    def test_result_has_required_keys(self):
        result = boss_agent.run(VALID_BRIEF)
        assert "status" in result
        assert "feedback" in result

    def test_status_is_approved_or_rejected(self):
        result = boss_agent.run(VALID_BRIEF)
        assert result["status"] in ("approved", "rejected")
