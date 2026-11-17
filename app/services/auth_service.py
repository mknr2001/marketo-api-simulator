"""Authentication service implementing OAuth-style client-credentials flow."""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.exceptions.types import InvalidTokenError
from app.models.database import AccessToken
from app.models.responses import TokenResponse
from app.repositories.token_repository import create_token, get_token_by_hash
from app.utilities.datetime_utils import ensure_utc, utc_now

logger = logging.getLogger(__name__)


def hash_token(raw_token: str, secret_key: str) -> str:
    """Compute HMAC-SHA256 hash of raw token for secure database storage."""
    return hmac.new(
        secret_key.encode("utf-8"),
        raw_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def authenticate_client(
    db: Session,
    grant_type: str,
    client_id: str,
    client_secret: str,
) -> TokenResponse:
    """Authenticate client credentials and issue an opaque bearer token.

    Stores only the HMAC-SHA256 hash in database. Returns raw token only here.
    """
    settings = get_settings()

    if grant_type != "client_credentials":
        logger.warning("Invalid grant_type attempted: %s", grant_type)
        raise InvalidTokenError(message="Unsupported grant_type")

    # Constant-time comparison to prevent timing attacks
    client_id_ok = hmac.compare_digest(client_id, settings.MOCK_CLIENT_ID)
    client_secret_ok = hmac.compare_digest(client_secret, settings.MOCK_CLIENT_SECRET)

    if not (client_id_ok and client_secret_ok):
        logger.warning("Authentication failed for client_id: %s", client_id)
        raise InvalidTokenError(message="Access token invalid")

    # Generate cryptographically secure opaque token
    raw_token = secrets.token_urlsafe(32)
    token_hashed = hash_token(raw_token, settings.TOKEN_HASH_SECRET)

    now = utc_now()
    ttl = settings.ACCESS_TOKEN_TTL_SECONDS
    expires = now + timedelta(seconds=ttl)

    create_token(
        db=db,
        token_hash=token_hashed,
        client_id=client_id,
        issued_at=now,
        expires_at=expires,
    )

    logger.info("Access token successfully issued for client_id: %s", client_id)

    return TokenResponse(
        access_token=raw_token,
        token_type="bearer",
        expires_in=ttl,
        scope="marketo.mock.api",
    )


def validate_bearer_token(db: Session, auth_header: str | None) -> AccessToken:
    """Validate bearer token from Authorization header against database.

    Requires:
    - Authorization header present and formatted as 'Bearer <token>'
    - Token hash found in database
    - Token not revoked
    - Token not expired
    """
    if not auth_header or not auth_header.startswith("Bearer "):
        raise InvalidTokenError(message="Access token invalid")

    raw_token = auth_header[7:].strip()
    if not raw_token:
        raise InvalidTokenError(message="Access token invalid")

    settings = get_settings()
    token_hashed = hash_token(raw_token, settings.TOKEN_HASH_SECRET)

    token_record = get_token_by_hash(db, token_hashed)
    if not token_record:
        raise InvalidTokenError(message="Access token invalid")

    if token_record.revoked_at is not None:
        raise InvalidTokenError(message="Access token invalid")

    expires_at = ensure_utc(token_record.expires_at)
    if expires_at is None or expires_at <= utc_now():
        raise InvalidTokenError(message="Access token invalid")

    return token_record
