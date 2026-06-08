"""
All SQLAlchemy ORM models for the Luxe Collective platform.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    ForeignKey, JSON, Boolean, Enum
)
from sqlalchemy.orm import relationship
from .database import Base
import enum


# ── Enums ──────────────────────────────────────────────────────────────────

class TaskStatus(str, enum.Enum):
    pending  = "pending"
    approved = "approved"
    rejected = "rejected"
    executed = "executed"
    failed   = "failed"


class AssetType(str, enum.Enum):
    logo        = "logo"
    graphic     = "graphic"
    accessory   = "accessory"
    lifestyle   = "lifestyle"
    other       = "other"


# ── Boss-Agent Approval Queue ──────────────────────────────────────────────

class Task(Base):
    __tablename__ = "tasks"

    id           = Column(Integer, primary_key=True, index=True)
    agent_id     = Column(String(10), nullable=False, index=True)
    task_type    = Column(String(80), nullable=False)
    description  = Column(Text, nullable=False)
    payload      = Column(JSON, nullable=True)
    status       = Column(String(20), default=TaskStatus.pending, index=True)
    boss_comment = Column(Text, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Design Assets ──────────────────────────────────────────────────────────

class DesignAsset(Base):
    __tablename__ = "design_assets"

    id           = Column(Integer, primary_key=True, index=True)
    task_id      = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    agent_id     = Column(String(10), nullable=False)
    asset_type   = Column(String(20), default=AssetType.other)
    name         = Column(String(200), nullable=False)
    description  = Column(Text, nullable=True)
    file_url     = Column(Text, nullable=True)     # S3 / local path
    thumbnail_url = Column(Text, nullable=True)
    metadata_    = Column("metadata", JSON, nullable=True)
    is_approved  = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", backref="design_assets")


# ── Activity Log ───────────────────────────────────────────────────────────

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id         = Column(Integer, primary_key=True, index=True)
    agent_id   = Column(String(10), nullable=False, index=True)
    event_type = Column(String(80), nullable=False)
    summary    = Column(Text, nullable=False)
    details    = Column(JSON, nullable=True)
    task_id    = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    task = relationship("Task", backref="activity_logs")


# ── Products & Orders ──────────────────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"

    id              = Column(Integer, primary_key=True, index=True)
    sku             = Column(String(50), unique=True, nullable=False, index=True)
    name            = Column(String(200), nullable=False)
    description     = Column(Text, nullable=True)
    category        = Column(String(80), nullable=True)
    price           = Column(Float, default=0.0)
    cost            = Column(Float, default=0.0)
    inventory_count = Column(Integer, default=0)
    image_url       = Column(Text, nullable=True)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    id           = Column(Integer, primary_key=True, index=True)
    customer_id  = Column(String(100), nullable=True)
    status       = Column(String(30), default="completed")
    total_amount = Column(Float, default=0.0)
    created_at   = Column(DateTime, default=datetime.utcnow, index=True)

    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id         = Column(Integer, primary_key=True, index=True)
    order_id   = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity   = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)

    order   = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


# ── Accessory Specs (Agent 04 output) ─────────────────────────────────────

class AccessorySpec(Base):
    __tablename__ = "accessory_specs"

    id              = Column(Integer, primary_key=True, index=True)
    task_id         = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    collection_name = Column(String(200), nullable=False)
    category        = Column(String(50), nullable=False)
    skus            = Column(JSON, nullable=True)   # list of SKU dicts
    created_at      = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", backref="accessory_specs")


# ── Marketing Campaigns (Agent 07 output) ─────────────────────────────────

class Campaign(Base):
    __tablename__ = "campaigns"

    id             = Column(Integer, primary_key=True, index=True)
    task_id        = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    name           = Column(String(200), nullable=False)
    channels       = Column(JSON, nullable=True)
    budget_usd     = Column(Float, default=0.0)
    target_audience = Column(JSON, nullable=True)
    creative_asset_ids = Column(JSON, nullable=True)
    flight_dates   = Column(JSON, nullable=True)
    kpis           = Column(JSON, nullable=True)
    status         = Column(String(30), default="scheduled")
    created_at     = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", backref="campaigns")


# ── Analytics Results (Agent 09 output) ───────────────────────────────────

class AnalyticsResult(Base):
    __tablename__ = "analytics_results"

    id            = Column(Integer, primary_key=True, index=True)
    task_id       = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    analysis_type = Column(String(80), nullable=False)
    params        = Column(JSON, nullable=True)
    result        = Column(JSON, nullable=True)
    status        = Column(String(20), default="requested")
    created_at    = Column(DateTime, default=datetime.utcnow)
    completed_at  = Column(DateTime, nullable=True)

    task = relationship("Task", backref="analytics_results")


# ── CX / Support Responses (Agent 10 output) ──────────────────────────────

class CXResponse(Base):
    __tablename__ = "cx_responses"

    id                = Column(Integer, primary_key=True, index=True)
    task_id           = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    ticket_id         = Column(Integer, nullable=True)
    issue_type        = Column(String(80), nullable=True)
    customer_tone     = Column(String(50), nullable=True)
    suggested_response = Column(Text, nullable=True)
    sent              = Column(Boolean, default=False)
    created_at        = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", backref="cx_responses")


# ── Users (for JWT auth) ───────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    role            = Column(String(30), default="viewer")   # "boss", "admin", "viewer"
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
