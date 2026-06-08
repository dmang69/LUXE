"""
/api/boss – task submission queue and Boss approval/rejection.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Any
import logging

from ..database import get_db
from ..auth import require_role
from .. import models
from ..workers.task_executor import execute_task

router = APIRouter(prefix="/api/boss", tags=["boss"])
logger = logging.getLogger(__name__)


# ── Schemas ────────────────────────────────────────────────────────────────

class TaskSubmit(BaseModel):
    agent_id: str
    task_type: str
    description: str
    payload: Optional[Any] = None


class ReviewDecision(BaseModel):
    approved: bool
    comment: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/submit", status_code=201)
def submit_task(body: TaskSubmit, db: Session = Depends(get_db)):
    """Agents call this to submit a task for Boss approval."""
    task = models.Task(
        agent_id=body.agent_id,
        task_type=body.task_type,
        description=body.description,
        payload=body.payload,
        status=models.TaskStatus.pending,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    _log(db, body.agent_id, "task_submitted", f"Submitted: {body.description}", task.id)
    logger.info("Task %d submitted by agent %s", task.id, body.agent_id)
    return {"task_id": task.id, "status": task.status}


@router.get("/pending")
def list_pending(
    db: Session = Depends(get_db),
    _boss=Depends(require_role("boss", "admin")),
):
    """Return all tasks awaiting Boss review."""
    tasks = (
        db.query(models.Task)
        .filter(models.Task.status == models.TaskStatus.pending)
        .order_by(models.Task.created_at.desc())
        .all()
    )
    return [_task_dict(t) for t in tasks]


@router.post("/review/{task_id}")
def review_task(
    task_id: int,
    body: ReviewDecision,
    db: Session = Depends(get_db),
    _boss=Depends(require_role("boss", "admin")),
):
    """Boss approves or rejects a pending task."""
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != models.TaskStatus.pending:
        raise HTTPException(status_code=400, detail=f"Task is already {task.status}")

    task.status = models.TaskStatus.approved if body.approved else models.TaskStatus.rejected
    task.boss_comment = body.comment
    db.commit()

    event = "task_approved" if body.approved else "task_rejected"
    _log(db, "boss", event, f"{event.replace('_', ' ').title()}: {task.description}", task_id)

    if body.approved:
        try:
            execute_task(db, task)
        except Exception as exc:
            logger.error("Executor failed for task %d: %s", task_id, exc)
            task.status = models.TaskStatus.failed
            db.commit()
            _log(db, "executor", "execution_failed", str(exc), task_id)

    db.refresh(task)
    return _task_dict(task)


@router.get("/tasks")
def list_all_tasks(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    _user=Depends(require_role("boss", "admin", "viewer")),
):
    q = db.query(models.Task)
    if status:
        q = q.filter(models.Task.status == status)
    if agent_id:
        q = q.filter(models.Task.agent_id == agent_id)
    tasks = q.order_by(models.Task.created_at.desc()).limit(limit).all()
    return [_task_dict(t) for t in tasks]


# ── Helpers ────────────────────────────────────────────────────────────────

def _task_dict(t: models.Task) -> dict:
    return {
        "id": t.id,
        "agent_id": t.agent_id,
        "task_type": t.task_type,
        "description": t.description,
        "payload": t.payload,
        "status": t.status,
        "boss_comment": t.boss_comment,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _log(db: Session, agent_id: str, event_type: str, summary: str, task_id: int = None):
    log = models.ActivityLog(
        agent_id=agent_id,
        event_type=event_type,
        summary=summary,
        task_id=task_id,
    )
    db.add(log)
    db.commit()
