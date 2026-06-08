"""
/api/activity – real-time activity log feed.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..auth import require_role
from .. import models

router = APIRouter(prefix="/api/activity", tags=["activity"])


@router.get("/recent")
def recent_activity(
    limit: int = 50,
    agent_id: Optional[str] = None,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _user=Depends(require_role("boss", "admin", "viewer")),
):
    q = db.query(models.ActivityLog).order_by(models.ActivityLog.created_at.desc())
    if agent_id:
        q = q.filter(models.ActivityLog.agent_id == agent_id)
    if event_type:
        q = q.filter(models.ActivityLog.event_type == event_type)
    logs = q.limit(limit).all()
    return [_log_dict(l) for l in logs]


@router.post("/log", status_code=201)
def write_log(
    agent_id: str,
    event_type: str,
    summary: str,
    details: Optional[dict] = None,
    task_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Agents can write directly to the activity log (no auth required for internal use)."""
    log = models.ActivityLog(
        agent_id=agent_id,
        event_type=event_type,
        summary=summary,
        details=details,
        task_id=task_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return _log_dict(log)


def _log_dict(l: models.ActivityLog) -> dict:
    return {
        "id": l.id,
        "agent_id": l.agent_id,
        "event_type": l.event_type,
        "summary": l.summary,
        "details": l.details,
        "task_id": l.task_id,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    }
