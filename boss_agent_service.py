import json
from datetime import UTC, datetime
from typing import List, Optional

from sqlalchemy import update
from sqlalchemy.orm import Session

import models


def _naive_utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


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
            .order_by(models.AgentTask.submitted_at.asc())
            .all()
        )

    def review_task(self, db: Session, task_id: int, decision: str) -> Optional[models.AgentTask]:
        task = db.query(models.AgentTask).filter(models.AgentTask.id == task_id).first()
        if not task:
            return None
        if task.status != "pending":
            raise ValueError("Only pending tasks can be reviewed")

        task.reviewed_at = _naive_utcnow()

        decision_upper = decision.upper().strip()
        feedback = decision.split(":", 1)[1].strip() if ":" in decision else decision

        if decision_upper.startswith("APPROVED"):
            task.status = "approved"
            task.approved_by = "Agent_01"
        elif decision_upper.startswith("REJECTED"):
            task.status = "rejected"
        else:
            raise ValueError("Decision must start with 'APPROVED' or 'REJECTED'")

        task.boss_feedback = feedback
        db.commit()
        db.refresh(task)
        return task

    def get_task(self, db: Session, task_id: int) -> Optional[models.AgentTask]:
        return db.query(models.AgentTask).filter(models.AgentTask.id == task_id).first()

    def get_approved_task_ids(self, db: Session) -> List[int]:
        return [
            task_id
            for (task_id,) in db.query(models.AgentTask.id)
            .filter(models.AgentTask.status == "approved")
            .all()
        ]

    def claim_task_for_execution(self, db: Session, task_id: int) -> Optional[models.AgentTask]:
        result = db.execute(
            update(models.AgentTask)
            .where(
                models.AgentTask.id == task_id,
                models.AgentTask.status == "approved",
            )
            .values(status="in_progress")
        )
        db.commit()
        if result.rowcount != 1:
            return None
        return self.get_task(db, task_id)

    def complete_task(
        self,
        db: Session,
        task_id: int,
        success: bool,
        result_data: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> Optional[models.AgentTask]:
        task = db.query(models.AgentTask).filter(models.AgentTask.id == task_id).first()
        if not task or task.status != "in_progress":
            return None

        task.status = "completed" if success else "failed"
        task.executed_at = _naive_utcnow()

        result = task.execution_result
        if result is None:
            result = models.TaskExecutionResult(task_id=task_id, success=success)
            db.add(result)
        result.success = success
        result.result_data = json.dumps(result_data) if result_data is not None else None
        result.error_message = error
        result.executed_at = _naive_utcnow()

        db.commit()
        db.refresh(task)
        return task


boss_agent_service = BossAgentService()
