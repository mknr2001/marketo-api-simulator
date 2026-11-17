"""Database engine and session factory."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def _build_engine(database_url: str) -> Any:
    """Create a SQLAlchemy engine for the given URL."""
    connect_args: dict[str, Any] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    eng = create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        echo=False,
    )

    # Enable WAL mode and foreign keys for SQLite
    if database_url.startswith("sqlite"):

        @event.listens_for(eng, "connect")
        def _set_sqlite_pragma(dbapi_conn: Any, _: Any) -> None:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return eng


settings = get_settings()
engine = _build_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and ensure cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
