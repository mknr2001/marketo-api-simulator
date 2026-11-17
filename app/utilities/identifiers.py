"""Request ID and export ID generation utilities."""

from __future__ import annotations

import re
import uuid


def generate_request_id() -> str:
    """Generate a UUID4-based request ID."""
    return str(uuid.uuid4())


def generate_export_id() -> str:
    """Generate a UUID4 export ID."""
    return str(uuid.uuid4())


# Pattern matching printable ASCII without control characters
_SAFE_REQUEST_ID_PATTERN = re.compile(r"^[\x20-\x7E]+$")


def sanitize_request_id(value: str | None, max_length: int = 100) -> str | None:
    """Validate and sanitize a caller-provided request ID.

    Returns None if the value is invalid (contains control characters,
    is too long, or is empty).
    """
    if not value:
        return None
    if len(value) > max_length:
        return None
    if not _SAFE_REQUEST_ID_PATTERN.match(value):
        return None
    return value
