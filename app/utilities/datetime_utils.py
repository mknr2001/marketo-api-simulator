"""Timezone normalization and UTC helpers."""

from __future__ import annotations

from datetime import UTC, datetime


def normalize_to_utc(dt: datetime) -> datetime:
    """Convert a datetime to UTC. If naive, assume UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure a datetime is UTC timezone-aware, handling SQLite naive datetimes."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def format_utc_iso(dt: datetime) -> str:
    """Format a datetime as UTC ISO-8601 string ending in Z.

    Example: '2026-11-02T06:44:01Z'
    """
    utc_dt = normalize_to_utc(dt)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(UTC)
