import httpx
from abc import ABC, abstractmethod
from typing import Any, Dict


class SpecializedAgentClient(ABC):
    """Base class for all specialized agent clients (Agents 02-10)."""

    def __init__(self, agent_id: str, boss_api_url: str = "http://localhost:8000/api/boss"):
        self.agent_id = agent_id
        self.boss_api_url = boss_api_url

    async def submit_for_approval(
        self,
        task_type: str,
        description: str,
        payload: Dict[str, Any],
    ) -> Dict:
        """Submit work to Boss Agent (Agent 01) for approval."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.boss_api_url}/submit",
                json={
                    "agent_id": self.agent_id,
                    "task_type": task_type,
                    "description": description,
                    "payload": payload,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_task_status(self, task_id: int) -> Dict:
        """Check the status of a previously submitted task."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.boss_api_url}/task/{task_id}")
            response.raise_for_status()
            return response.json()

    @abstractmethod
    async def create_work(self, **kwargs) -> Dict:
        """Create work to be submitted for Boss Agent approval."""
        pass
