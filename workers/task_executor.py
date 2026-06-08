import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Dict

from sqlalchemy.orm import Session

import models
from boss_agent_service import boss_agent_service

logger = logging.getLogger(__name__)


class TaskExecutor:
    """Background worker that polls for Boss-Agent-approved tasks and executes them."""

    POLL_INTERVAL = 5  # seconds

    def __init__(self, db_session_factory: Callable[[], Session]):
        self.db_session_factory = db_session_factory
        self.running = False

    async def start(self) -> None:
        self.running = True
        logger.info("TaskExecutor started")
        while self.running:
            try:
                await self._process_approved_tasks()
            except Exception as exc:
                logger.error("TaskExecutor error: %s", exc)
            await asyncio.sleep(self.POLL_INTERVAL)

    def stop(self) -> None:
        self.running = False
        logger.info("TaskExecutor stopped")

    async def _process_approved_tasks(self) -> None:
        db = self.db_session_factory()
        try:
            approved = (
                db.query(models.AgentTask)
                .filter(models.AgentTask.status == "approved")
                .all()
            )
            for task in approved:
                logger.info("Executing task %d (agent %s)", task.id, task.agent_id)
                boss_agent_service.mark_task_executing(db, task.id)
                try:
                    result = self._execute(task)
                    boss_agent_service.complete_task(db, task.id, True, result)
                    logger.info("Task %d completed", task.id)
                except Exception as exc:
                    logger.error("Task %d failed: %s", task.id, exc)
                    boss_agent_service.complete_task(db, task.id, False, None, str(exc))
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Execution routing
    # ------------------------------------------------------------------

    def _execute(self, task: models.AgentTask) -> Dict:
        payload = json.loads(task.payload)
        handler = self._get_handler(task.agent_id, task.task_type)
        return handler(task, payload)

    def _get_handler(self, agent_id: str, task_type: str):
        handlers = {
            ("02", "design_concept"): self._handle_logo_design,
            ("03", "design_concept"): self._handle_graphic_design,
        }
        return handlers.get((agent_id, task_type), self._handle_generic)

    @staticmethod
    def _handle_logo_design(task: models.AgentTask, payload: dict) -> Dict:
        return {
            "logo_variations": payload.get("variations", []),
            "style_guide": payload.get("style_guide", {}),
            "production_ready": True,
            "completed_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _handle_graphic_design(task: models.AgentTask, payload: dict) -> Dict:
        return {
            "collection_designs": payload.get("designs", []),
            "production_notes": payload.get("production_notes", []),
            "print_ready_files": True,
            "completed_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _handle_generic(task: models.AgentTask, payload: dict) -> Dict:
        return {
            "message": f"Executed {task.task_type} for agent {task.agent_id}",
            "payload": payload,
            "completed_at": datetime.utcnow().isoformat(),
        }
