"""Inclusive UTC calendar-day range calculation."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta


def calculate_inclusive_days(start_at: datetime, end_at: datetime) -> int:
    """Calculate the inclusive number of UTC calendar days.

    Formula: (UTC_date(endAt) - UTC_date(startAt)).days + 1

    Examples:
        2026-11-01T00:00:00Z to 2026-11-01T23:59:59Z -> 1
        2026-11-01T12:00:00Z to 2026-11-03T10:00:00Z -> 3
    """
    start_date = start_at.astimezone(UTC).date()
    end_date = end_at.astimezone(UTC).date()
    return (end_date - start_date).days + 1


def generate_daily_dates(start_at: datetime, end_at: datetime) -> list[date]:
    """Return a list of all included UTC calendar dates in the range."""
    start_date = start_at.astimezone(UTC).date()
    end_date = end_at.astimezone(UTC).date()
    dates: list[date] = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates
