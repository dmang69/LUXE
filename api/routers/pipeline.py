"""
Pipeline orchestration for the Luxe Collective multi-agent workflow.
This module contains the run_pipeline() function and its DB helper utilities,
keeping route definitions separate in tasks.py.
"""
import json
import logging

from sqlalchemy.orm import Session

from database import SessionLocal
from models import AgentResult, Task, TaskLog, TaskStatus
from agents import boss_agent, graphic_agent, logo_agent, print_agent

logger = logging.getLogger(__name__)


# ── DB helpers ────────────────────────────────────────────────────────────────

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
