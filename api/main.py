"""
Luxe Collective – FastAPI Application Entry Point
"""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers.tasks import router as tasks_router

logging.basicConfig(level=logging.INFO)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501").split(",")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,api").split(",")

app = FastAPI(
    title="Luxe Collective – Multi-Agent Platform",
    description=(
        "Boss Agent → Logo Designer → Graphic Designer → Print Sourcing.\n\n"
        "Submit a creative brief and watch four AI agents collaborate in real time."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "service": "luxe-collective-api"}


@app.on_event("startup")
def on_startup():
    init_db()
