"""
Tasks router – CRUD + workflow trigger.
POST /tasks          → create task → immediately run full pipeline
GET  /tasks          → list all tasks
GET  /tasks/{id}     → task detail with all agent results and logs
DELETE /tasks/{id}   → remove task
"""
import json
import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import AgentResult, Task, TaskLog, TaskStatus
from schemas import TaskCreate, TaskDetail, TaskOut

from agents import boss_agent, graphic_agent, logo_agent, print_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _log(db: Session, task_id: int, agent: str, action: str, message: str):
    entry = TaskLog(task_id=task_id, agent=agent, action=action, message=message)
    db.add(entry)
    db.commit()


def _save_result(
    db: Session,
    task_id: int,
    agent_id: str,
    agent_name: str,
    result_type: str,
    content: dict,
    result_status: str,
):
    record = AgentResult(
        task_id=task_id,
        agent_id=agent_id,
        agent_name=agent_name,
        result_type=result_type,
        content=json.dumps(content, indent=2),
        status=result_status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _set_status(db: Session, task: Task, new_status: str):
    task.status = new_status
    db.commit()
    db.refresh(task)


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_pipeline(task_id: int):
    """
    Runs the full multi-agent pipeline for a task.
    Runs in a background thread so the POST endpoint returns immediately.
    """
    from database import SessionLocal  # import here to avoid circular at module level

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return

        task_data = {
            "title": task.title,
            "brand_name": task.brand_name,
            "product_type": task.product_type,
            "style_description": task.style_description,
            "quantity": task.quantity,
            "budget_usd": task.budget_usd,
        }

        # ── Agent 01: Boss Review ──────────────────────────────────────────────
        _set_status(db, task, TaskStatus.BOSS_REVIEW)
        _log(db, task_id, "Agent 01 – Boss", "review_start", "Reviewing creative brief…")

        boss_result = boss_agent.run(task_data)
        boss_status = boss_result.get("status", "rejected")

        _save_result(
            db, task_id,
            "agent_01", "Agent 01 – Boss Agent",
            "approval",
            boss_result,
            boss_status,
        )
        _log(db, task_id, "Agent 01 – Boss", "review_complete", boss_result.get("feedback", ""))

        if boss_status == "rejected":
            _set_status(db, task, TaskStatus.REJECTED)
            _log(db, task_id, "System", "pipeline_end", "Pipeline stopped: task rejected by Boss Agent.")
            return

        _set_status(db, task, TaskStatus.APPROVED)

        # ── Agent 02: Logo Design ─────────────────────────────────────────────
        _set_status(db, task, TaskStatus.LOGO_DESIGN)
        _log(db, task_id, "Agent 02 – Logo", "design_start", "Generating logo concept…")

        logo_result = logo_agent.run(task_data, boss_result.get("feedback", ""))
        _save_result(
            db, task_id,
            "agent_02", "Agent 02 – Logo Designer",
            "logo_concept",
            logo_result,
            "success",
        )
        _log(
            db, task_id, "Agent 02 – Logo", "design_complete",
            f"Concept: {logo_result.get('concept_name', 'Created')}",
        )

        # ── Agent 03: Graphic Design ──────────────────────────────────────────
        _set_status(db, task, TaskStatus.GRAPHIC_DESIGN)
        _log(db, task_id, "Agent 03 – Graphic", "design_start", "Creating garment graphic specification…")

        graphic_result = graphic_agent.run(task_data, logo_result)
        _save_result(
            db, task_id,
            "agent_03", "Agent 03 – Graphic Designer",
            "graphic",
            graphic_result,
            "success",
        )
        _log(
            db, task_id, "Agent 03 – Graphic", "design_complete",
            f"Graphic: {graphic_result.get('graphic_name', 'Created')} — "
            f"{graphic_result.get('print_technique', '')}",
        )

        # ── Agent 05: Print Sourcing ──────────────────────────────────────────
        _set_status(db, task, TaskStatus.PRINT_SOURCING)
        _log(db, task_id, "Agent 05 – Print", "sourcing_start", "Querying vendor database…")

        print_result = print_agent.run(task_data, graphic_result)
        _save_result(
            db, task_id,
            "agent_05", "Agent 05 – Print Sourcing",
            "print_quote",
            print_result,
            "success",
        )
        rec = print_result.get("recommended_vendor") or {}
        _log(
            db, task_id, "Agent 05 – Print", "sourcing_complete",
            f"Recommended: {rec.get('vendor_name', 'N/A')} @ ${rec.get('total_cost_usd', 'N/A')} total",
        )

        # ── Done ──────────────────────────────────────────────────────────────
        _set_status(db, task, TaskStatus.COMPLETED)
        _log(db, task_id, "System", "pipeline_complete", "All agents completed successfully. 🎉")

    except Exception as exc:
        logger.exception("Pipeline error for task %s", task_id)
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                _set_status(db, task, TaskStatus.FAILED)
                _log(db, task_id, "System", "pipeline_error", str(exc))
        except Exception:
            pass
    finally:
        db.close()


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
