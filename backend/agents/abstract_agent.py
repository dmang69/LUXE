"""
Abstract base class for all Luxe specialist agents.
"""
import os
import httpx
from typing import Any, Optional


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class SpecializedAgentClient:
    """
    Base class providing a common `submit_for_approval` method.
    Each specialist subclass calls this to push a task into the Boss queue.
    """

    def __init__(self, agent_id: str, boss_api_url: Optional[str] = None):
        self.agent_id = agent_id
        self.boss_api_url = boss_api_url or f"{API_BASE_URL}/api/boss"

    async def submit_for_approval(
        self,
        task_type: str,
        description: str,
        payload: Any = None,
    ) -> dict:
        """POST the task to /api/boss/submit and return the response JSON."""
        body = {
            "agent_id": self.agent_id,
            "task_type": task_type,
            "description": description,
            "payload": payload,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{self.boss_api_url}/submit", json=body)
            resp.raise_for_status()
            return resp.json()

    async def log_activity(
        self,
        event_type: str,
        summary: str,
        details: Optional[dict] = None,
        task_id: Optional[int] = None,
    ) -> None:
        """Write an entry to the activity log."""
        params = {
            "agent_id": self.agent_id,
            "event_type": event_type,
            "summary": summary,
        }
        if task_id is not None:
            params["task_id"] = task_id
        body = details or {}
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                await client.post(
                    f"{API_BASE_URL}/api/activity/log",
                    params=params,
                    json=body,
                )
            except Exception:
                pass  # logging should never crash the agent
