"""Health and readiness probe endpoints."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", summary="Liveness probe")
def liveness() -> dict[str, str]:
    """Check if the service process is alive."""
    return {"status": "live"}


@router.get("/ready", summary="Readiness probe")
def readiness(db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    """Check if service is ready to receive traffic by verifying database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        raise HTTPException(status_code=503, detail={"status": "not_ready"}) from exc
