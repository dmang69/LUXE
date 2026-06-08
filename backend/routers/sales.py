"""
/api/admin/sales – KPI endpoints for the dashboard.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timedelta
from typing import Optional

from ..database import get_db
from ..auth import require_role
from .. import models

router = APIRouter(prefix="/api/admin/sales", tags=["sales"])


@router.get("/summary")
def sales_summary(
    db: Session = Depends(get_db),
    _user=Depends(require_role("boss", "admin")),
):
    """Aggregate KPIs: revenue, orders, AOV, top-line metrics."""
    now = datetime.utcnow()
    start_30 = now - timedelta(days=30)
    start_prev_30 = now - timedelta(days=60)

    # Current period
    cur = (
        db.query(
            func.count(models.Order.id).label("orders"),
            func.coalesce(func.sum(models.Order.total_amount), 0).label("revenue"),
        )
        .filter(models.Order.created_at >= start_30, models.Order.status == "completed")
        .one()
    )

    # Previous period
    prev = (
        db.query(
            func.count(models.Order.id).label("orders"),
            func.coalesce(func.sum(models.Order.total_amount), 0).label("revenue"),
        )
        .filter(
            models.Order.created_at.between(start_prev_30, start_30),
            models.Order.status == "completed",
        )
        .one()
    )

    revenue = float(cur.revenue)
    prev_revenue = float(prev.revenue)
    orders = int(cur.orders)
    prev_orders = int(prev.orders)
    aov = revenue / orders if orders else 0.0

    # Unique customers (approximated via customer_id)
    unique_customers = (
        db.query(func.count(func.distinct(models.Order.customer_id)))
        .filter(models.Order.created_at >= start_30, models.Order.status == "completed")
        .scalar() or 0
    )

    # Inventory value
    inventory_value = (
        db.query(func.coalesce(func.sum(models.Product.price * models.Product.inventory_count), 0))
        .filter(models.Product.is_active == True)
        .scalar() or 0
    )

    revenue_delta = revenue - prev_revenue
    orders_delta  = orders - prev_orders

    return {
        "revenue_30d":       round(revenue, 2),
        "revenue_delta":     round(revenue_delta, 2),
        "revenue_delta_pct": round((revenue_delta / prev_revenue * 100) if prev_revenue else 0, 1),
        "orders_30d":        orders,
        "orders_delta":      orders_delta,
        "aov":               round(aov, 2),
        "unique_customers":  int(unique_customers),
        "inventory_value":   round(float(inventory_value), 2),
        "cav":               round(0.0, 2),   # placeholder – requires ad-spend data; key kept for backwards compat
        "cac":               round(0.0, 2),   # alias used by dashboard
        "turnover":          round(0.0, 1),   # placeholder – requires COGS data
    }


@router.get("/trend")
def sales_trend(
    days: int = 7,
    db: Session = Depends(get_db),
    _user=Depends(require_role("boss", "admin")),
):
    """Daily revenue for the last `days` days."""
    now  = datetime.utcnow()
    labels, values = [], []

    for i in range(days - 1, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end   = day_start + timedelta(days=1)
        total = (
            db.query(func.coalesce(func.sum(models.Order.total_amount), 0))
            .filter(
                models.Order.created_at >= day_start,
                models.Order.created_at < day_end,
                models.Order.status == "completed",
            )
            .scalar()
        )
        labels.append(day_start.strftime("%b %d"))
        values.append(round(float(total), 2))

    return {"labels": labels, "values": values}


@router.get("/top-products")
def top_products(
    limit: int = 5,
    db: Session = Depends(get_db),
    _user=Depends(require_role("boss", "admin")),
):
    """Top N products by units sold."""
    rows = (
        db.query(
            models.Product.id,
            models.Product.name,
            models.Product.sku,
            models.Product.price,
            models.Product.cost,
            func.coalesce(func.sum(models.OrderItem.quantity), 0).label("units_sold"),
            func.coalesce(func.sum(models.OrderItem.quantity * models.OrderItem.unit_price), 0).label("revenue"),
        )
        .join(models.OrderItem, models.OrderItem.product_id == models.Product.id, isouter=True)
        .group_by(models.Product.id)
        .order_by(func.sum(models.OrderItem.quantity).desc().nullslast())
        .limit(limit)
        .all()
    )

    result = []
    for rank, row in enumerate(rows, 1):
        units    = int(row.units_sold)
        revenue  = float(row.revenue)
        cost     = float(row.cost or 0) * units
        margin   = f"{((revenue - cost) / revenue * 100):.0f}%" if revenue else "N/A"
        result.append({
            "Rank":    rank,
            "Product": row.name,
            "SKU":     row.sku,
            "Units":   units,
            "Revenue": f"${revenue:,.2f}",
            "Margin":  margin,
        })

    return result


@router.get("/products")
def list_products(
    limit: int = 100,
    db: Session = Depends(get_db),
    _user=Depends(require_role("boss", "admin", "viewer")),
):
    products = (
        db.query(models.Product)
        .filter(models.Product.is_active == True)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": p.id, "sku": p.sku, "name": p.name,
            "category": p.category, "price": p.price,
            "inventory_count": p.inventory_count,
        }
        for p in products
    ]


# ── Internal helper used by task_executor ─────────────────────────────────

def _run_analysis_query(db: Session, analysis_type: str, params: dict) -> dict:
    """Run a basic SQL-based analysis; returns a JSON-serialisable dict."""
    if analysis_type == "sales_trend":
        days = int(params.get("days", 7))
        now = datetime.utcnow()
        rows = []
        for i in range(days - 1, -1, -1):
            day = now - timedelta(days=i)
            start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            end   = start + timedelta(days=1)
            total = (
                db.query(func.coalesce(func.sum(models.Order.total_amount), 0))
                .filter(models.Order.created_at >= start,
                        models.Order.created_at < end,
                        models.Order.status == "completed")
                .scalar()
            )
            rows.append({"date": start.strftime("%Y-%m-%d"), "revenue": float(total)})
        return {"rows": rows}

    if analysis_type == "inventory":
        products = (
            db.query(models.Product)
            .filter(models.Product.is_active == True)
            .all()
        )
        return {
            "total_skus": len(products),
            "total_units": sum(p.inventory_count for p in products),
            "inventory_value": sum(p.price * p.inventory_count for p in products),
        }

    if analysis_type == "top_products":
        limit = int(params.get("limit", 5))
        rows = (
            db.query(
                models.Product.name,
                models.Product.sku,
                func.coalesce(func.sum(models.OrderItem.quantity), 0).label("units"),
            )
            .join(models.OrderItem, models.OrderItem.product_id == models.Product.id, isouter=True)
            .group_by(models.Product.id)
            .order_by(func.sum(models.OrderItem.quantity).desc().nullslast())
            .limit(limit)
            .all()
        )
        return {"rows": [{"name": r.name, "sku": r.sku, "units": int(r.units)} for r in rows]}

    return {"note": f"Analysis '{analysis_type}' not yet implemented in query runner."}
