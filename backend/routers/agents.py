"""
/api/agents – read-only views per specialist agent.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..auth import require_role
from .. import models

router = APIRouter(prefix="/api/agents", tags=["agents"])


# ── Agent 04 – Accessories ────────────────────────────────────────────────

@router.get("/04/specs")
def accessory_specs(
    limit: int = 20,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    _user=Depends(require_role("boss", "admin", "viewer")),
):
    q = db.query(models.AccessorySpec)
    if category:
        q = q.filter(models.AccessorySpec.category == category)
    specs = q.order_by(models.AccessorySpec.created_at.desc()).limit(limit).all()
    return [
        {
            "id": s.id,
            "collection_name": s.collection_name,
            "category": s.category,
            "sku_count": len(s.skus) if s.skus else 0,
            "skus": s.skus,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in specs
    ]


# ── Agent 07 – Marketing Campaigns ───────────────────────────────────────

@router.get("/07/campaigns")
def campaigns(
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _user=Depends(require_role("boss", "admin", "viewer")),
):
    q = db.query(models.Campaign)
    if status:
        q = q.filter(models.Campaign.status == status)
    camps = q.order_by(models.Campaign.created_at.desc()).limit(limit).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "channels": c.channels,
            "budget_usd": c.budget_usd,
            "status": c.status,
            "flight_dates": c.flight_dates,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in camps
    ]


# ── Agent 09 – Analytics Results ─────────────────────────────────────────

@router.get("/09/analytics")
def analytics_results(
    analysis_type: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    _user=Depends(require_role("boss", "admin", "viewer")),
):
    q = db.query(models.AnalyticsResult)
    if analysis_type:
        q = q.filter(models.AnalyticsResult.analysis_type == analysis_type)
    results = q.order_by(models.AnalyticsResult.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "analysis_type": r.analysis_type,
            "params": r.params,
            "status": r.status,
            "result": r.result,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in results
    ]


# ── Agent 10 – CX Responses ───────────────────────────────────────────────

@router.get("/10/cx-responses")
def cx_responses(
    limit: int = 20,
    sent: Optional[bool] = None,
    db: Session = Depends(get_db),
    _user=Depends(require_role("boss", "admin", "viewer")),
):
    q = db.query(models.CXResponse)
    if sent is not None:
        q = q.filter(models.CXResponse.sent == sent)
    responses = q.order_by(models.CXResponse.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "ticket_id": r.ticket_id,
            "issue_type": r.issue_type,
            "suggested_response": r.suggested_response,
            "sent": r.sent,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in responses
    ]
