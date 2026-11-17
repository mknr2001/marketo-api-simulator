"""FastAPI exception handlers that produce Marketo-style error responses."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.exceptions.types import MarketoAPIError
from app.models.responses import MarketoError, MarketoErrorResponse
from app.utilities.identifiers import generate_request_id

logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str:
    """Extract request ID from request state, or generate a new one."""
    return getattr(request.state, "request_id", generate_request_id())


def _build_error_response(
    request_id: str,
    status_code: int,
    error_code: str,
    message: str,
) -> JSONResponse:
    """Build a Marketo-style error JSON response."""
    body = MarketoErrorResponse(
        requestId=request_id,
        errors=[MarketoError(code=error_code, message=message)],
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers={"X-Request-Id": request_id},
    )


async def marketo_api_error_handler(request: Request, exc: MarketoAPIError) -> JSONResponse:
    """Handle MarketoAPIError exceptions."""
    request_id = _get_request_id(request)
    logger.warning(
        "API error: code=%s message=%s",
        exc.error_code,
        exc.message,
        extra={"request_id": request_id, "error_code": exc.error_code},
    )
    return _build_error_response(request_id, exc.status_code, exc.error_code, exc.message)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Convert FastAPI / Pydantic validation errors into Marketo-style format."""
    request_id = _get_request_id(request)
    messages: list[str] = []
    for err in exc.errors():
        loc = " -> ".join(str(part) for part in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        messages.append(f"{loc}: {msg}" if loc else msg)
    combined = "; ".join(messages)
    logger.warning(
        "Validation error: %s",
        combined,
        extra={"request_id": request_id},
    )
    return _build_error_response(request_id, 422, "1040", combined)


async def pydantic_validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle raw Pydantic ValidationError (not wrapped by FastAPI)."""
    request_id = _get_request_id(request)
    messages: list[str] = []
    for err in exc.errors():
        loc = " -> ".join(str(part) for part in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        messages.append(f"{loc}: {msg}" if loc else msg)
    combined = "; ".join(messages)
    logger.warning(
        "Pydantic validation error: %s",
        combined,
        extra={"request_id": request_id},
    )
    return _build_error_response(request_id, 422, "1040", combined)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler that hides internal details."""
    request_id = _get_request_id(request)
    logger.exception(
        "Unhandled exception",
        extra={"request_id": request_id},
    )
    return _build_error_response(
        request_id, 500, "1040", "An internal error occurred"
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application."""
    app.add_exception_handler(MarketoAPIError, marketo_api_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ValidationError, pydantic_validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore[arg-type]
