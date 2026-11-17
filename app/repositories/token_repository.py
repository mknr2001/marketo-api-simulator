"""Repository for access tokens."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.database import AccessToken
from app.utilities.datetime_utils import utc_now


def create_token(
    db: Session,
    token_hash: str,
    client_id: str,
    issued_at: datetime,
    expires_at: datetime,
) -> AccessToken:
    """Persist a new hashed access token."""
    token = AccessToken(
        token_hash=token_hash,
        client_id=client_id,
        issued_at=issued_at,
        expires_at=expires_at,
        revoked_at=None,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_token_by_hash(db: Session, token_hash: str) -> AccessToken | None:
    """Retrieve an access token by its hash."""
    stmt = select(AccessToken).where(AccessToken.token_hash == token_hash)
    return db.execute(stmt).scalar_one_or_none()


def revoke_token(db: Session, token_id: int) -> None:
    """Mark a token as revoked."""
    stmt = select(AccessToken).where(AccessToken.id == token_id)
    token = db.execute(stmt).scalar_one_or_none()
    if token:
        token.revoked_at = utc_now()
        db.commit()
