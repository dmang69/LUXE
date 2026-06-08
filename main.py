import asyncio
import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import Base, engine, SessionLocal
from routes import auth_router, products_router, cart_router, orders_router, boss_router
from workers.task_executor import TaskExecutor

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Create tables ─────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Luxe Collective API",
    description=(
        "Premium AI-powered fashion e-commerce platform for Luxe Collective. "
        "Integrates Boss Agent (Agent 01) approval workflow with specialised "
        "design and operations agents."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(boss_router)

# ── Background worker ─────────────────────────────────────────────────────────
_executor: TaskExecutor | None = None


@app.on_event("startup")
async def startup_event():
    global _executor
    _executor = TaskExecutor(SessionLocal)
    asyncio.create_task(_executor.start())
    logger.info("Luxe Collective API started – TaskExecutor running")


@app.on_event("shutdown")
async def shutdown_event():
    if _executor:
        _executor.stop()
    logger.info("Luxe Collective API shut down")


# ── System endpoints ──────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
def health_check():
    return {"status": "healthy", "service": "Luxe Collective API"}


@app.get("/", tags=["system"])
def root():
    return {
        "message": "Welcome to the Luxe Collective API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENV", "development") == "development",
        log_level="info",
    )
