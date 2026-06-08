import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

import models


class BossAgentService:
    """Central approval hub (Agent 01 – The Brand Architect)."""

    def submit_task(
        self,
        db: Session,
        agent_id: str,
        task_type: str,
        description: str,
        payload: dict,
    ) -> models.AgentTask:
        task = models.AgentTask(
            agent_id=agent_id,
            task_type=task_type,
            description=description,
            payload=json.dumps(payload),
            status="pending",
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def get_pending_tasks(self, db: Session) -> List[models.AgentTask]:
        return (
            db.query(models.AgentTask)
            .filter(models.AgentTask.status == "pending")
            .all()
        )

    def review_task(self, db: Session, task_id: int, decision: str) -> models.AgentTask:
        task = db.query(models.AgentTask).filter(models.AgentTask.id == task_id).first()
        if not task:
            return None

        task.reviewed_at = datetime.utcnow()

        decision_upper = decision.upper().strip()
        feedback = decision.split(":", 1)[1].strip() if ":" in decision else decision

        if decision_upper.startswith("APPROVED"):
            task.status = "approved"
            task.approved_by = "Agent_01"
        else:
            task.status = "rejected"

        task.boss_feedback = feedback
        db.commit()
        db.refresh(task)
        return task

    def get_task(self, db: Session, task_id: int) -> Optional[models.AgentTask]:
        return db.query(models.AgentTask).filter(models.AgentTask.id == task_id).first()

    def get_approved_task(self, db: Session, task_id: int) -> Optional[models.AgentTask]:
        return (
            db.query(models.AgentTask)
            .filter(
                models.AgentTask.id == task_id,
                models.AgentTask.status == "approved",
            )
            .first()
        )

    def mark_task_executing(self, db: Session, task_id: int) -> None:
        task = db.query(models.AgentTask).filter(models.AgentTask.id == task_id).first()
        if task:
            task.status = "in_progress"
            db.commit()

    def complete_task(
        self,
        db: Session,
        task_id: int,
        success: bool,
        result_data: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> None:
        task = db.query(models.AgentTask).filter(models.AgentTask.id == task_id).first()
        if task:
            task.status = "completed" if success else "failed"
            task.executed_at = datetime.utcnow()
            result = models.TaskExecutionResult(
                task_id=task_id,
                success=success,
                result_data=json.dumps(result_data) if result_data else None,
                error_message=error,
            )
            db.add(result)
            db.commit()


boss_agent_service = BossAgentService()
