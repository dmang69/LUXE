import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

_DATABASE_URL = os.getenv("DATABASE_URL")
if not _DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Copy .env.template to .env and configure it."
    )

engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    import models  # noqa: F401 – registers model classes with Base metadata
    Base.metadata.create_all(bind=engine)
