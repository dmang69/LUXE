"""
Luxe Collective – Dashboard helpers
API client functions, UI constants, and badge utility used by dashboard.py.
"""
import os

import requests

API_BASE = os.getenv("API_BASE_URL", "http://api:8000")

# ── Status display constants ──────────────────────────────────────────────────

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


# ── Badge helper ──────────────────────────────────────────────────────────────


def badge(status: str) -> str:
    emoji = STATUS_EMOJI.get(status, "❓")
    return f'<span class="agent-badge status-{status}">{emoji} {status.replace("_", " ").title()}</span>'
