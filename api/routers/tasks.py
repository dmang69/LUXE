"""
Tasks router – CRUD + workflow trigger.
POST /tasks          → create task → immediately run full pipeline
GET  /tasks          → list all tasks
GET  /tasks/{id}     → task detail with all agent results and logs
DELETE /tasks/{id}   → remove task
"""
import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import AgentResult, Task, TaskLog
from schemas import TaskCreate, TaskDetail, TaskOut

from routers.pipeline import run_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    background_tasks.add_task(run_pipeline, task.id)
    return task


@router.get("/", response_model=List[TaskOut])
def list_tasks(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Task).order_by(Task.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{task_id}", response_model=TaskDetail)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # delete children first
    db.query(TaskLog).filter(TaskLog.task_id == task_id).delete()
    db.query(AgentResult).filter(AgentResult.task_id == task_id).delete()
    db.delete(task)
    db.commit()

