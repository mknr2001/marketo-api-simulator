"""Export job lifecycle service for creation and enqueueing."""

from __future__ import annotations

import logging
import random
from datetime import timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.exceptions.types import (
    ExportNotFoundError,
    InvalidDateRangeError,
    InvalidExportStateError,
    InvalidRequestError,
    MaxRecordsExceededError,
    TooManyJobsError,
)
from app.generators.activity_generator import (
    calculate_daily_record_counts,
    generate_deterministic_seed,
)
from app.models.requests import CreateExportRequest
from app.models.responses import ExportJobResult
from app.repositories.export_repository import (
    count_active_jobs,
    create_export_job,
    get_export_job,
    update_job_enqueued,
)
from app.utilities.date_range import calculate_inclusive_days
from app.utilities.datetime_utils import format_utc_iso, normalize_to_utc, utc_now
from app.utilities.identifiers import generate_export_id

logger = logging.getLogger(__name__)


def create_export(
    db: Session,
    request: CreateExportRequest,
    request_id: str,
) -> ExportJobResult:
    """Create a new export job in 'Created' state."""
    settings = get_settings()

    start_at = normalize_to_utc(request.filter.createdAt.startAt)
    end_at = normalize_to_utc(request.filter.createdAt.endAt)

    num_days = calculate_inclusive_days(start_at, end_at)
    if num_days > settings.MAX_EXPORT_RANGE_DAYS:
        raise InvalidDateRangeError(
            f"Date range exceeds maximum allowed {settings.MAX_EXPORT_RANGE_DAYS} days"
        )

    export_id = generate_export_id()
    seed = generate_deterministic_seed(
        export_id=export_id,
        activity_type_ids=request.filter.activityTypeIds,
        start_at=start_at,
        end_at=end_at,
    )

    job = create_export_job(
        db=db,
        export_id=export_id,
        request_id=request_id,
        activity_type_ids=request.filter.activityTypeIds,
        start_at=start_at,
        end_at=end_at,
        number_of_days=num_days,
        deterministic_seed=seed,
    )

    logger.info(
        "Export job created: export_id=%s days=%d seed=%d",
        export_id,
        num_days,
        seed,
        extra={"export_id": export_id, "request_id": request_id},
    )

    return ExportJobResult(
        exportId=job.export_id,
        status="Created",
        createdAt=format_utc_iso(job.created_at),
        format="TSV",
    )


def enqueue_export(
    db: Session,
    export_id: str,
    request_id: str,
    mock_record_count: int | None = None,
) -> ExportJobResult:
    """Enqueue an export job, calculate deterministic counts, and set time delays."""
    settings = get_settings()

    job = get_export_job(db, export_id, for_update=True)
    if not job:
        raise ExportNotFoundError(export_id)

    if job.status != "Created":
        logger.warning(
            "Job already enqueued: export_id=%s status=%s",
            export_id,
            job.status,
            extra={"export_id": export_id},
        )
        raise InvalidExportStateError("Export job has already been enqueued")

    # Validate test override header
    if mock_record_count is not None:
        if not settings.is_test_env:
            raise InvalidRequestError("X-Mock-Record-Count is not allowed in production")
        if mock_record_count < 0:
            raise InvalidRequestError("X-Mock-Record-Count must be >= 0")

    now = utc_now()

    # Enforce active job limit within transaction
    active_count = count_active_jobs(db, now)
    if active_count >= settings.MAX_ACTIVE_EXPORT_JOBS:
        logger.warning("Active export job queue full: %d active jobs", active_count)
        raise TooManyJobsError()

    queued_at = now
    started_at = queued_at + timedelta(seconds=settings.QUEUE_DELAY_SECONDS)
    finished_at = started_at + timedelta(seconds=settings.PROCESSING_DELAY_SECONDS)

    if mock_record_count is not None and mock_record_count == 0:
        daily_counts = [0] * job.number_of_days
        total_records = 0
    else:
        seed = job.deterministic_seed or 0
        rng = random.Random(seed)
        daily_counts = calculate_daily_record_counts(
            rng=rng,
            num_days=job.number_of_days,
            min_per_day=settings.MIN_RECORDS_PER_DAY,
            max_per_day=settings.MAX_RECORDS_PER_DAY,
        )
        total_records = sum(daily_counts)

    if total_records > settings.MAX_RECORDS_PER_EXPORT:
        raise MaxRecordsExceededError(total_records, settings.MAX_RECORDS_PER_EXPORT)

    job = update_job_enqueued(
        db=db,
        job=job,
        queued_at=queued_at,
        started_at=started_at,
        finished_at=finished_at,
        daily_counts=daily_counts,
        number_of_records=total_records,
    )

    logger.info(
        "Export job enqueued: export_id=%s records=%d queued_at=%s finished_at=%s",
        export_id,
        total_records,
        format_utc_iso(queued_at),
        format_utc_iso(finished_at),
        extra={"export_id": export_id, "request_id": request_id},
    )

    return ExportJobResult(
        exportId=job.export_id,
        status="Queued",
        createdAt=format_utc_iso(job.created_at),
        queuedAt=format_utc_iso(queued_at),
        format="TSV",
    )
