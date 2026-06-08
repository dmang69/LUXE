"""
LUXE COLLECTIVE - Extended API Routes
Boss Agent, Design Assets, Sales Analytics, and Activity Log endpoints.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import ActivityLog, AgentTask, DesignAsset, Order, OrderItem, Product, User
from security import require_admin

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_admin_user(current_user: User = Depends(require_admin)) -> User:
    return current_user


def log_activity(db: Session, agent_id: str, action: str, meta: dict = None) -> None:
    """Record an activity log entry."""
    entry = ActivityLog(
        agent_id=agent_id,
        action=action,
        metadata=json.dumps(meta) if meta else None,
    )
    db.add(entry)
    db.commit()


# ─── Boss Agent Router ────────────────────────────────────────────────────────

boss_router = APIRouter(prefix="/api/boss", tags=["boss-agent"])


@boss_router.get("/pending", response_model=List[dict])
def get_pending_tasks(
    db: Session = Depends(get_db),
    _: User = Depends(_get_admin_user),
):
    """Return all pending tasks awaiting Boss Agent review."""
    tasks = db.query(AgentTask).filter(AgentTask.status == "pending").all()
    return [
        {
            "id": t.id,
            "agent_id": t.agent_id,
            "task_type": t.task_type,
            "description": t.description,
            "payload": json.loads(t.payload) if t.payload else {},
            "status": t.status,
            "submitted_at": t.submitted_at,
            "reviewed_at": t.reviewed_at,
            "boss_feedback": t.boss_feedback,
        }
        for t in tasks
    ]


@boss_router.get("/tasks", response_model=List[dict])
def list_tasks(
    status: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(_get_admin_user),
):
    """Flexible task query (supports comma-separated agent_id list)."""
    query = db.query(AgentTask)
    if status:
        query = query.filter(AgentTask.status == status)
    if agent_id:
        ids = [a.strip() for a in agent_id.split(",")]
        query = query.filter(AgentTask.agent_id.in_(ids))
    if task_type:
        query = query.filter(AgentTask.task_type == task_type)
    tasks = query.order_by(AgentTask.submitted_at.desc()).all()
    return [
        {
            "id": t.id,
            "agent_id": t.agent_id,
            "task_type": t.task_type,
            "description": t.description,
            "payload": json.loads(t.payload) if t.payload else {},
            "status": t.status,
            "submitted_at": t.submitted_at,
            "reviewed_at": t.reviewed_at,
            "boss_feedback": t.boss_feedback,
        }
        for t in tasks
    ]


@boss_router.post("/tasks/{task_id}/approve")
def approve_task(
    task_id: int,
    feedback: str = Query("Approved by Boss Agent."),
    db: Session = Depends(get_db),
    _: User = Depends(_get_admin_user),
):
    """Approve a pending task."""
    task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "approved"
    task.boss_feedback = feedback
    task.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    log_activity(db, task.agent_id, f"Task approved: {task.description}", {"task_id": task.id})
    return {"status": "approved", "task_id": task_id}


@boss_router.post("/tasks/{task_id}/reject")
def reject_task(
    task_id: int,
    feedback: str = Query("Rejected by Boss Agent."),
    db: Session = Depends(get_db),
    _: User = Depends(_get_admin_user),
):
    """Reject a pending task."""
    task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "rejected"
    task.boss_feedback = feedback
    task.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    log_activity(db, task.agent_id, f"Task rejected: {task.description}", {"task_id": task.id})
    return {"status": "rejected", "task_id": task_id}


# ─── Design Asset Router ──────────────────────────────────────────────────────

design_router = APIRouter(prefix="/api/design", tags=["design"])


@design_router.get("/approved", response_model=List[dict])
def get_approved_designs(
    db: Session = Depends(get_db),
    _: User = Depends(_get_admin_user),
):
    """Return all approved design assets (from Agents 02 & 03)."""
    assets = (
        db.query(DesignAsset)
        .join(AgentTask, DesignAsset.task_id == AgentTask.id)
        .filter(
            AgentTask.status == "approved",
            AgentTask.agent_id.in_(["02", "03"]),
            AgentTask.task_type == "design_concept",
        )
        .all()
    )
    result = []
    for asset in assets:
        data = json.loads(asset.asset_data)
        result.append({
            "id": asset.id,
            "task_id": asset.task_id,
            "agent_id": asset.task.agent_id,
            "asset_type": asset.asset_type,
            "asset_data": data,
            "created_at": asset.created_at,
        })
    return result


# ─── Sales & Performance Router ───────────────────────────────────────────────

sales_router = APIRouter(prefix="/api/admin/sales", tags=["admin-sales"])


@sales_router.get("/summary")
def get_sales_summary(
    db: Session = Depends(get_db),
    _: User = Depends(_get_admin_user),
):
    """Key KPI cards for the dashboard."""
    today = datetime.now(timezone.utc).date()

    today_revenue = (
        db.query(func.sum(Order.total_amount))
        .filter(func.date(Order.created_at) == today)
        .scalar() or 0
    )

    visitors_today = 1200  # replace with real analytics tracker
    orders_today = (
        db.query(func.count(Order.id))
        .filter(func.date(Order.created_at) == today)
        .scalar() or 0
    )
    conversion = orders_today / visitors_today if visitors_today else 0

    week_ago = today - timedelta(days=6)
    top_product = (
        db.query(
            Product.name,
            func.sum(OrderItem.quantity).label("units"),
            func.sum(OrderItem.quantity * OrderItem.price).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.created_at >= week_ago)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .first()
    )
    top_product_name = top_product[0] if top_product else "-"
    top_units = int(top_product[1]) if top_product else 0
    top_revenue = float(top_product[2]) if top_product else 0

    roas = 4.2  # replace with actual ad spend calculation

    return {
        "revenue_today": round(float(today_revenue), 2),
        "conversion_rate": round(conversion * 100, 2),
        "top_product": top_product_name,
        "top_units": top_units,
        "top_revenue": round(top_revenue, 2),
        "roas": round(roas, 2),
    }


@sales_router.get("/top-products")
def get_top_products(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    _: User = Depends(_get_admin_user),
):
    """Top-selling products for the table in Screen 4."""
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    rows = (
        db.query(
            Product.name.label("product"),
            Product.id.label("sku"),
            func.sum(OrderItem.quantity).label("units"),
            func.sum(OrderItem.quantity * OrderItem.price).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.created_at >= week_ago)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "Rank": idx + 1,
            "Product": r.product,
            "SKU": f"SKU-{r.sku:03d}",
            "Units": int(r.units),
            "Revenue": f"${float(r.revenue):.2f}",
            "Margin": "~70%",
        }
        for idx, r in enumerate(rows)
    ]


@sales_router.get("/trend")
def get_sales_trend(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    _: User = Depends(_get_admin_user),
):
    """Daily revenue for the line chart in Screen 4."""
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=days - 1)
    daily = (
        db.query(
            func.date(Order.created_at).label("day"),
            func.sum(Order.total_amount).label("revenue"),
        )
        .filter(Order.created_at >= start)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )
    date_rev = {row.day: float(row.revenue) for row in daily}
    labels = [(start + timedelta(days=i)).strftime("%m/%d") for i in range(days)]
    values = [date_rev.get(str(start + timedelta(days=i)), 0.0) for i in range(days)]
    return {"labels": labels, "values": values}


# ─── Activity Log Router ──────────────────────────────────────────────────────

activity_router = APIRouter(prefix="/api/activity", tags=["activity"])


@activity_router.get("/recent")
def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(_get_admin_user),
):
    """Return the most recent activity log entries (newest first)."""
    logs = (
        db.query(ActivityLog)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "time": log.created_at.strftime("%H:%M:%S"),
            "agent": log.agent_id,
            "action": log.action,
            "meta": json.loads(log.metadata) if log.metadata else None,
        }
        for log in logs
    ]
