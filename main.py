import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import SessionLocal, init_database
from routes import auth_router, products_router, cart_router, orders_router, boss_router
from workers.task_executor import TaskExecutor

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def _parse_cors_origins() -> list[str]:
    origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
    if os.getenv("ENV", "development").lower() == "production" and "*" in origins:
        raise RuntimeError("CORS_ORIGINS cannot include '*' when ENV=production")
    return origins


def _task_worker_enabled() -> bool:
    return os.getenv("ENABLE_TASK_WORKER", "false").lower() in {"1", "true", "yes", "on"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()

    executor: TaskExecutor | None = None
    executor_task: asyncio.Task | None = None
    if _task_worker_enabled():
        executor = TaskExecutor(SessionLocal)
        executor_task = asyncio.create_task(executor.start())
        logger.info("TaskExecutor enabled")
    else:
        logger.info("TaskExecutor disabled; set ENABLE_TASK_WORKER=true to enable polling")

    try:
        yield
    finally:
        if executor and executor_task:
            executor.stop()
            await executor_task

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
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
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
