"""SHA-256 checksum utilities."""

from __future__ import annotations

import hashlib


def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 checksum and return as 'sha256:<hex>' string."""
    digest = hashlib.sha256(data).hexdigest()
    return f"sha256:{digest}"


def verify_checksum(data: bytes, expected: str) -> bool:
    """Verify data matches the expected 'sha256:<hex>' checksum."""
    actual = compute_sha256(data)
    return actual == expected
