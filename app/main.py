"""FastAPI application initialization and middleware configuration."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.openapi.utils import get_openapi

from app.api.auth import router as auth_router
from app.api.exports import router as exports_router
from app.api.health import router as health_router
from app.config import get_settings
from app.database import engine
from app.exceptions.handlers import register_exception_handlers
from app.logging_config import setup_logging
from app.models.database import Base
from app.utilities.identifiers import generate_request_id, sanitize_request_id

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Application startup and shutdown lifecycle management."""
    settings = get_settings()
    setup_logging(log_level=settings.LOG_LEVEL)
    logger.info("Starting %s in %s environment", settings.APP_NAME, settings.APP_ENV)

    # Initialize tables automatically
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified and initialized successfully")

    yield

    logger.info("Shutting down %s", settings.APP_NAME)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Marketo Bulk Activity API Simulator",
        description=(
            "A high-fidelity simulator for the Marketo Bulk Activity Export API.\n\n"
            "### Workflow Sequence\n"
            "1. **Authenticate**: Obtain Bearer access token via `POST /identity/oauth/token`.\n"
            "2. **Create Export**: Create export job for activity type 2 (Fill Out Form) via `POST /bulk/v1/activities/export/create.json`.\n"
            "3. **Enqueue Export**: Enqueue job via `POST /bulk/v1/activities/export/{exportId}/enqueue.json`.\n"
            "4. **Poll Status**: Check job status via `GET /bulk/v1/activities/export/{exportId}/status.json` until `Completed`.\n"
            "5. **Download TSV**: Stream the 21-column TSV file via `GET /bulk/v1/activities/export/{exportId}/file.json`.\n\n"
            "**Note on File Endpoint:** Successful response is a TSV file, even though the endpoint ends in `file.json`."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────
    @app.middleware("http")
    async def request_tracing_and_logging_middleware(request: Request, call_next: Any) -> Response:
        """Trace request IDs and log structured execution metrics."""
        raw_header = request.headers.get("X-Request-Id")
        req_id = sanitize_request_id(raw_header) or generate_request_id()
        request.state.request_id = req_id

        start_time = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Attach request ID header to all responses
        response.headers["X-Request-Id"] = req_id

        # Skip logging health checks to reduce noise
        if not request.url.path.startswith("/health"):
            logger.info(
                "%s %s completed with %d in %sms",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                extra={
                    "request_id": req_id,
                    "method": request.method,
                    "path": request.url.path,
                    "response_status": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

        return response

    # ── Exception Handlers ────────────────────────────────────────
    register_exception_handlers(app)

    # ── Root Redirect ─────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root_redirect() -> Response:
        return Response(status_code=307, headers={"Location": "/docs"})

    # ── Routers ───────────────────────────────────────────────────
    app.include_router(auth_router)
    app.include_router(exports_router)
    app.include_router(health_router)

    # ── Custom OpenAPI Security Scheme ────────────────────────────
    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        openapi_schema["components"] = openapi_schema.get("components", {})
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "opaque",
                "description": "Enter the access token issued by `/identity/oauth/token`",
            }
        }

        # Apply BearerAuth security to bulk export routes
        for path, path_item in openapi_schema.get("paths", {}).items():
            if path.startswith("/bulk/"):
                for method in path_item.values():
                    if isinstance(method, dict):
                        method["security"] = [{"BearerAuth": []}]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    return app


app = create_app()
