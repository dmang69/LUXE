"""
Task Executor – runs approved tasks from the Boss queue.
Called synchronously from the review endpoint; long-running tasks should
be dispatched to a background worker (Celery, RQ, etc.) in production.
"""
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from ..models import (
    Task, TaskStatus, DesignAsset, AccessorySpec, Campaign,
    AnalyticsResult, CXResponse, Product, ActivityLog,
)

logger = logging.getLogger(__name__)


def execute_task(db: Session, task: Task) -> None:
    """
    Synchronous dispatcher.  For async AI calls we use asyncio.run().
    """
    logger.info("Executing task %d type=%s agent=%s", task.id, task.task_type, task.agent_id)

    try:
        handler = _HANDLERS.get(task.task_type)
        if handler is None:
            logger.warning("No handler for task_type=%s – marking executed", task.task_type)
        else:
            handler(db, task)

        task.status = TaskStatus.executed
        db.commit()
        _log(db, "executor", "task_executed",
             f"Executed: {task.description}", task.id)

    except Exception as exc:
        task.status = TaskStatus.failed
        db.commit()
        _log(db, "executor", "execution_failed", str(exc), task.id)
        raise


# ── Handlers ───────────────────────────────────────────────────────────────

def _handle_design_concept(db: Session, task: Task) -> None:
    """Agent 04 – store accessory spec + trigger image generation."""
    p = task.payload or {}
    spec = AccessorySpec(
        task_id=task.id,
        collection_name=p.get("collection", "Unnamed"),
        category=p.get("category", "accessory"),
        skus=p.get("skus", []),
    )
    db.add(spec)

    # Also create a DesignAsset entry for each SKU concept
    for sku in p.get("skus", []):
        asset = DesignAsset(
            task_id=task.id,
            agent_id=task.agent_id,
            asset_type="accessory",
            name=sku.get("name", "Accessory"),
            description=sku.get("description", ""),
            metadata_=sku,
            is_approved=True,
        )
        db.add(asset)

        # Fire-and-forget image generation if a prompt is present
        if sku.get("image_prompt"):
            asyncio.run(_generate_and_attach_image(db, asset, sku["image_prompt"]))

    db.commit()


def _handle_catalog_update(db: Session, task: Task) -> None:
    """Agent 06 – apply bulk product updates."""
    p = task.payload or {}
    product_ids = p.get("product_ids", [])
    updates     = p.get("updates", {})

    for pid in product_ids:
        product = db.query(Product).filter(Product.id == pid).first()
        if not product:
            continue
        for key, value in updates.items():
            if hasattr(product, key):
                setattr(product, key, value)
        product.updated_at = datetime.utcnow()

    db.commit()


def _handle_create_product(db: Session, task: Task) -> None:
    """Agent 06 – create a new product listing."""
    p = task.payload or {}
    product = Product(
        sku=p.get("sku", f"SKU-{task.id}"),
        name=p.get("name", "New Product"),
        description=p.get("description", ""),
        price=float(p.get("price", 0)),
        category=p.get("category", "general"),
        is_active=True,
    )
    db.add(product)
    db.commit()

    if p.get("image_prompt"):
        asyncio.run(_generate_and_attach_image(db, None, p["image_prompt"],
                                               product_id=product.id))


def _handle_marketing_campaign(db: Session, task: Task) -> None:
    """Agent 07 – persist approved campaign."""
    p = task.payload or {}
    campaign = Campaign(
        task_id=task.id,
        name=p.get("campaign_name", "Campaign"),
        channels=p.get("channels", []),
        budget_usd=float(p.get("budget_usd", 0)),
        target_audience=p.get("target_audience", {}),
        creative_asset_ids=p.get("creative_asset_ids", []),
        flight_dates=p.get("flight_dates", {}),
        kpis=p.get("kpis", []),
        status="scheduled",
    )
    db.add(campaign)
    db.commit()


def _handle_content_creation(db: Session, task: Task) -> None:
    """Agent 08 – call LLM and write copy to product descriptions."""
    p = task.payload or {}
    copy_type       = p.get("copy_type", "description")
    product_ids     = p.get("product_ids", [])
    tone            = p.get("tone", "luxury")
    product_context = p.get("product_context", [])

    generated = {}
    for prod in product_context:
        pid  = prod.get("id")
        name = prod.get("name", f"Product {pid}")
        prompt = (
            f"Write a {copy_type} for the luxury fashion product '{name}'. "
            f"Tone: {tone}. Max 150 words."
        )
        copy = asyncio.run(_run_text_gen(prompt))
        generated[str(pid)] = copy

        product = db.query(Product).filter(Product.id == pid).first()
        if product and copy_type == "description":
            product.description = copy
            product.updated_at  = datetime.utcnow()

    task.payload = {**p, "generated_copy": generated}
    db.commit()


def _handle_analysis_request(db: Session, task: Task) -> None:
    """Agent 09 – run SQL-based analysis and store result."""
    p = task.payload or {}
    result_row = AnalyticsResult(
        task_id=task.id,
        analysis_type=p.get("analysis_type", "unknown"),
        params=p.get("params", {}),
        status="running",
    )
    db.add(result_row)
    db.commit()

    try:
        from ..routers.sales import _run_analysis_query
        result = _run_analysis_query(db, p.get("analysis_type"), p.get("params", {}))
    except Exception as exc:
        result = {"error": str(exc)}

    result_row.result       = result
    result_row.status       = "completed"
    result_row.completed_at = datetime.utcnow()
    db.commit()


def _handle_cx_response(db: Session, task: Task) -> None:
    """Agent 10 – generate LLM response draft and store it."""
    p = task.payload or {}
    ticket_id     = p.get("ticket_id")
    issue_type    = p.get("issue_type", "general")
    customer_tone = p.get("customer_tone", "neutral")
    context       = p.get("context", {})

    prompt = (
        f"Draft an empathetic, professional customer service response for a "
        f"{customer_tone} customer with a '{issue_type}' issue. "
        f"Context: {context}. Keep it under 120 words."
    )
    suggested = asyncio.run(_run_text_gen(prompt))

    cx = CXResponse(
        task_id=task.id,
        ticket_id=ticket_id,
        issue_type=issue_type,
        customer_tone=customer_tone,
        suggested_response=suggested,
        sent=False,
    )
    db.add(cx)
    task.payload = {**p, "suggested_response": suggested}
    db.commit()


def _handle_blog_post(db: Session, task: Task) -> None:
    """Agent 08 – generate a blog post and store it as a design asset (content)."""
    p = task.payload or {}
    prompt = (
        f"Write a {p.get('word_count', 600)}-word luxury fashion blog post "
        f"titled '{p.get('title', 'Untitled')}'. "
        f"Topic: {p.get('topic', '')}. "
        f"Keywords: {', '.join(p.get('keywords', []))}."
    )
    content = asyncio.run(_run_text_gen(prompt, max_tokens=800))

    asset = DesignAsset(
        task_id=task.id,
        agent_id=task.agent_id,
        asset_type="other",
        name=p.get("title", "Blog Post"),
        description=content[:500] if content else "",
        metadata_={"content": content, "type": "blog_post"},
        is_approved=True,
    )
    db.add(asset)
    task.payload = {**p, "content": content}
    db.commit()


def _handle_promo_code(db: Session, task: Task) -> None:
    """Agent 07 – log the promo code (in production, push to e-commerce platform)."""
    p = task.payload or {}
    _log(db, task.agent_id, "promo_code_created",
         f"Promo code {p.get('code')} ({p.get('discount_pct')}% off) approved",
         task.id)


def _handle_cx_outreach(db: Session, task: Task) -> None:
    """Agent 10 – log outreach (in production, send via email/SMS API)."""
    p = task.payload or {}
    _log(db, task.agent_id, "cx_outreach_queued",
         f"Outreach to {len(p.get('customer_ids', []))} customer(s) queued",
         task.id)


def _handle_return_request(db: Session, task: Task) -> None:
    """Agent 10 – log return initiation."""
    p = task.payload or {}
    _log(db, task.agent_id, "return_processed",
         f"Return processed for order #{p.get('order_id')}: {p.get('reason')}",
         task.id)


def _handle_recurring_analysis(db: Session, task: Task) -> None:
    """Agent 09 – store recurring schedule (cron picks it up)."""
    p = task.payload or {}
    _log(db, task.agent_id, "recurring_analysis_scheduled",
         f"Recurring {p.get('frequency')} {p.get('analysis_type')} scheduled",
         task.id)


# ── Handler registry ───────────────────────────────────────────────────────

_HANDLERS = {
    "design_concept":       _handle_design_concept,
    "catalog_update":       _handle_catalog_update,
    "create_product":       _handle_create_product,
    "marketing_campaign":   _handle_marketing_campaign,
    "content_creation":     _handle_content_creation,
    "blog_post":            _handle_blog_post,
    "analysis_request":     _handle_analysis_request,
    "recurring_analysis":   _handle_recurring_analysis,
    "cx_response":          _handle_cx_response,
    "cx_outreach":          _handle_cx_outreach,
    "return_request":       _handle_return_request,
    "promo_code":           _handle_promo_code,
}


# ── Async helpers (run inside asyncio.run) ─────────────────────────────────

async def _run_text_gen(prompt: str, max_tokens: int = 500) -> str:
    from ..services.ai_text import generate_text
    return await generate_text(prompt, max_tokens=max_tokens)


async def _generate_and_attach_image(
    db: Session,
    asset,
    prompt: str,
    product_id: int = None,
) -> None:
    from ..services.ai_image import generate_image
    from ..services.storage import upload_asset, unique_filename

    image_bytes = await generate_image(prompt)
    if not image_bytes:
        return

    filename = unique_filename("png")
    url = await upload_asset(image_bytes, filename, "image/png", "generated")

    if asset is not None:
        asset.file_url      = url
        asset.thumbnail_url = url
        db.commit()

    if product_id is not None:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.image_url = url
            db.commit()


# ── Utility ────────────────────────────────────────────────────────────────

def _log(db: Session, agent_id: str, event_type: str, summary: str, task_id: int = None):
    log = ActivityLog(
        agent_id=agent_id,
        event_type=event_type,
        summary=summary,
        task_id=task_id,
    )
    db.add(log)
    db.commit()
