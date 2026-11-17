"""FastAPI dependencies for authentication, database session, and request tracing."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions.types import InvalidTokenError
from app.models.database import AccessToken
from app.services.auth_service import validate_bearer_token
from app.utilities.identifiers import generate_request_id, sanitize_request_id


def get_request_id(
    request: Request,
    x_request_id: Annotated[str | None, Header(alias="X-Request-Id")] = None,
) -> str:
    """Extract and sanitize caller X-Request-Id or generate a fresh UUID4."""
    req_id = sanitize_request_id(x_request_id)
    if not req_id:
        req_id = generate_request_id()
    request.state.request_id = req_id
    return req_id


def get_current_token(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> AccessToken:
    """Validate bearer token from Authorization header.

    Strictly rejects access tokens in URL query parameters.
    """
    if "access_token" in request.query_params or "token" in request.query_params:
        raise InvalidTokenError(message="Access token in query parameters is not permitted")

    return validate_bearer_token(db=db, auth_header=authorization)
