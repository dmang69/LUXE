"""
Luxe Collective – FastAPI backend entry point.

Run:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .auth import hash_password
from . import models
from .database import SessionLocal

# ── Routers ────────────────────────────────────────────────────────────────
from .routers import auth, boss, design, activity, sales, agents

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

LOCAL_ASSET_DIR = os.getenv("LOCAL_ASSET_DIR", "assets")
os.makedirs(LOCAL_ASSET_DIR, exist_ok=True)


# ── Startup / shutdown ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _seed_default_users()
    _seed_demo_data()
    logger.info("Luxe backend is live 👑")
    yield
    logger.info("Luxe backend shutting down.")


def _seed_default_users():
    """Create default boss / admin accounts if they don't exist."""
    db = SessionLocal()
    try:
        for username, password, role in [
            ("boss",  os.getenv("BOSS_PASSWORD",  "boss-luxe"),  "boss"),
            ("admin", os.getenv("ADMIN_PASSWORD", "admin-luxe"), "admin"),
        ]:
            if not db.query(models.User).filter(models.User.username == username).first():
                db.add(models.User(
                    username=username,
                    hashed_password=hash_password(password),
                    role=role,
                ))
        db.commit()
    finally:
        db.close()


def _seed_demo_data():
    """Insert sample products + orders so the dashboard looks populated on first run."""
    db = SessionLocal()
    try:
        if db.query(models.Product).count() > 0:
            return  # already seeded

        import random
        from datetime import datetime, timedelta

        categories = ["handbag", "wallet", "footwear", "jewellery", "apparel"]
        products   = []
        for i in range(1, 21):
            cat  = categories[i % len(categories)]
            prod = models.Product(
                sku=f"{cat.upper()[:3]}-{i:04d}",
                name=f"Luxe {cat.title()} {i}",
                description=f"A premium {cat} crafted for the discerning collector.",
                category=cat,
                price=round(random.uniform(80, 600), 2),
                cost=round(random.uniform(20, 150), 2),
                inventory_count=random.randint(5, 100),
            )
            db.add(prod)
            products.append(prod)
        db.commit()
        for p in products:
            db.refresh(p)

        # Generate 90 days of orders
        now = datetime.utcnow()
        for d in range(90):
            day   = now - timedelta(days=d)
            count = random.randint(1, 8)
            for _ in range(count):
                order = models.Order(
                    customer_id=f"cust-{random.randint(1, 500)}",
                    status="completed",
                    created_at=day - timedelta(hours=random.randint(0, 23)),
                )
                db.add(order)
                db.commit()
                db.refresh(order)

                n_items = random.randint(1, 3)
                total   = 0.0
                for _ in range(n_items):
                    prod = random.choice(products)
                    qty  = random.randint(1, 2)
                    item = models.OrderItem(
                        order_id=order.id,
                        product_id=prod.id,
                        quantity=qty,
                        unit_price=prod.price,
                    )
                    db.add(item)
                    total += qty * prod.price
                order.total_amount = round(total, 2)
                db.commit()

        logger.info("Demo data seeded: 20 products, 90 days of orders.")
    except Exception as exc:
        logger.error("Demo seeding failed: %s", exc)
        db.rollback()
    finally:
        db.close()


# ── App ────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Luxe Collective Command Center API",
    description="Backend for the Luxe AI agent workforce.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploaded/generated assets
app.mount("/static", StaticFiles(directory=LOCAL_ASSET_DIR), name="static")

# Routers
app.include_router(auth.router)
app.include_router(boss.router)
app.include_router(design.router)
app.include_router(activity.router)
app.include_router(sales.router)
app.include_router(agents.router)


@app.get("/")
def root():
    return {"message": "Luxe Collective API is live 👑", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
