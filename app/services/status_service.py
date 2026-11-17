"""Status derivation and completed job reconciliation service."""

from __future__ import annotations

import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.exceptions.types import ExportNotFoundError
from app.generators.activity_generator import generate_activity_records, generate_tsv_bytes
from app.models.database import ExportJob
from app.models.responses import ExportJobResult
from app.repositories.export_repository import get_export_job, update_job_completed
from app.utilities.checksum import compute_sha256
from app.utilities.date_range import generate_daily_dates
from app.utilities.datetime_utils import ensure_utc, format_utc_iso, utc_now

logger = logging.getLogger(__name__)


def derive_status(job: ExportJob, now: datetime) -> str:
    """Derive effective status from persisted timestamps.

    Rules:
        Created:    queued_at is None
        Queued:     now < started_at
        Processing: now >= started_at and now < finished_at
        Completed:  now >= finished_at
        Failed:     status == "Failed"
    """
    if job.status == "Failed":
        return "Failed"
    if job.queued_at is None:
        return "Created"
    started_at = ensure_utc(job.started_at)
    finished_at = ensure_utc(job.finished_at)
    if started_at is not None and now < started_at:
        return "Queued"
    if finished_at is not None and now < finished_at:
        return "Processing"
    return "Completed"


def ensure_completed_metrics(db: Session, job: ExportJob) -> ExportJob:
    """Ensure completed job has file size and checksum generated and persisted (idempotent)."""
    if job.file_size_bytes is not None and job.file_checksum_sha256 is not None:
        return job

    start_at = ensure_utc(job.start_at) or utc_now()
    end_at = ensure_utc(job.end_at) or utc_now()

    # Generate the deterministic TSV bytes to compute checksum and size
    daily_counts = json.loads(job.daily_record_counts_json or "[]")
    daily_dates = generate_daily_dates(start_at, end_at)
    seed = job.deterministic_seed or 0

    records = generate_activity_records(
        export_id=job.export_id,
        seed=seed,
        start_at=start_at,
        end_at=end_at,
        daily_counts=daily_counts,
        daily_dates=daily_dates,
    )
    tsv_bytes = generate_tsv_bytes(records)
    file_size = len(tsv_bytes)
    checksum = compute_sha256(tsv_bytes)

    job = update_job_completed(
        db=db,
        job=job,
        file_size_bytes=file_size,
        file_checksum_sha256=checksum,
    )

    logger.info(
        "Export job finalized metrics: export_id=%s size=%d checksum=%s",
        job.export_id,
        file_size,
        checksum,
        extra={"export_id": job.export_id},
    )
    return job


def get_export_status(
    db: Session,
    export_id: str,
    request_id: str,
) -> ExportJobResult:
    """Return the status response for the specified export job."""
    job = get_export_job(db, export_id)
    if not job:
        raise ExportNotFoundError(export_id)

    now = utc_now()
    status = derive_status(job, now)

    result = ExportJobResult(
        exportId=job.export_id,
        status=status,
        createdAt=format_utc_iso(job.created_at),
        format="TSV",
    )

    if status in ("Queued", "Processing", "Completed") and job.queued_at:
        result.queuedAt = format_utc_iso(job.queued_at)

    if status in ("Processing", "Completed") and job.started_at:
        result.startedAt = format_utc_iso(job.started_at)

    if status == "Completed":
        # Finalize metrics if first time Completed
        job = ensure_completed_metrics(db, job)
        if job.finished_at:
            result.finishedAt = format_utc_iso(job.finished_at)
        result.numberOfDays = job.number_of_days
        result.numberOfRecords = job.number_of_records
        result.fileSize = job.file_size_bytes
        result.fileChecksum = job.file_checksum_sha256

    return result
