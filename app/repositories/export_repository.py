"""Repository for export jobs."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.database import ExportJob


def create_export_job(
    db: Session,
    export_id: str,
    request_id: str,
    activity_type_ids: list[int],
    start_at: datetime,
    end_at: datetime,
    number_of_days: int,
    deterministic_seed: int,
) -> ExportJob:
    """Persist a newly created export job in 'Created' status."""
    job = ExportJob(
        export_id=export_id,
        request_id=request_id,
        activity_type_ids=json.dumps(activity_type_ids),
        start_at=start_at,
        end_at=end_at,
        number_of_days=number_of_days,
        output_format="TSV",
        status="Created",
        deterministic_seed=deterministic_seed,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_export_job(db: Session, export_id: str, for_update: bool = False) -> ExportJob | None:
    """Retrieve an export job by its UUID export_id."""
    stmt = select(ExportJob).where(ExportJob.export_id == export_id)
    if for_update and db.bind and db.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update()
    return db.execute(stmt).scalar_one_or_none()


def update_job_enqueued(
    db: Session,
    job: ExportJob,
    queued_at: datetime,
    started_at: datetime,
    finished_at: datetime,
    daily_counts: list[int],
    number_of_records: int,
) -> ExportJob:
    """Update job to 'Queued' status with timing and record count calculations."""
    job.status = "Queued"
    job.queued_at = queued_at
    job.started_at = started_at
    job.finished_at = finished_at
    job.daily_record_counts_json = json.dumps(daily_counts)
    job.number_of_records = number_of_records
    db.commit()
    db.refresh(job)
    return job


def update_job_completed(
    db: Session,
    job: ExportJob,
    file_size_bytes: int,
    file_checksum_sha256: str,
) -> ExportJob:
    """Update job with cached file size and checksum on first completion."""
    job.file_size_bytes = file_size_bytes
    job.file_checksum_sha256 = file_checksum_sha256
    # Note: status is logically derived from timestamps, but we update status column as well
    job.status = "Completed"
    db.commit()
    db.refresh(job)
    return job


def update_job_failed(
    db: Session,
    job: ExportJob,
    error_code: str,
    error_message: str,
) -> ExportJob:
    """Mark job as failed."""
    job.status = "Failed"
    job.error_code = error_code
    job.error_message = error_message
    db.commit()
    db.refresh(job)
    return job


def count_active_jobs(db: Session, current_time: datetime) -> int:
    """Count active export jobs (Queued or Processing state).

    A job is active if:
    - It has been enqueued (queued_at is not null)
    - It is not Failed
    - current_time < finished_at (still queued or processing)
    """
    stmt = select(ExportJob).where(
        and_(
            ExportJob.queued_at.isnot(None),
            ExportJob.status != "Failed",
        )
    )
    if db.bind and db.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update()
    jobs = db.execute(stmt).scalars().all()
    active_count = 0
    now_utc = current_time if current_time.tzinfo is not None else current_time.replace(tzinfo=UTC)
    for job in jobs:
        fin = job.finished_at
        if fin is not None:
            if fin.tzinfo is None:
                fin = fin.replace(tzinfo=UTC)
            if fin > now_utc:
                active_count += 1
    return active_count
