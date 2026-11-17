"""Authentication router for OAuth-style token exchange."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_request_id
from app.models.responses import TokenResponse
from app.services.auth_service import authenticate_client

router = APIRouter(prefix="/identity/oauth", tags=["Authentication"])


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Generate OAuth access token",
    description="Authenticate client credentials and obtain an opaque Bearer access token.",
)
def issue_token(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    request_id: Annotated[str, Depends(get_request_id)],
    grant_type: Annotated[str, Form(description="Grant type, must be 'client_credentials'")],
    client_id: Annotated[str, Form(description="Client ID")],
    client_secret: Annotated[str, Form(description="Client secret")],
) -> TokenResponse:
    """Issue a bearer access token using client credentials."""
    response.headers["X-Request-Id"] = request_id
    return authenticate_client(
        db=db,
        grant_type=grant_type,
        client_id=client_id,
        client_secret=client_secret,
    )
