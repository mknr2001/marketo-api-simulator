"""Marketo Bulk Activity Export endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response
from fastapi.responses import Response as RawResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_token, get_request_id
from app.models.database import AccessToken
from app.models.requests import CreateExportRequest
from app.models.responses import MarketoSuccessResponse
from app.services.export_service import create_export, enqueue_export
from app.services.file_service import get_export_file
from app.services.status_service import get_export_status

router = APIRouter(prefix="/bulk/v1/activities/export", tags=["Bulk Export"])


@router.post(
    "/create.json",
    response_model=MarketoSuccessResponse,
    summary="Create activity export job",
    description="Initialize a new bulk activity export job for activity type 2 (Fill Out Form). Format is strictly TSV.",
)
def create_export_job(
    request: CreateExportRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    current_token: Annotated[AccessToken, Depends(get_current_token)],
    request_id: Annotated[str, Depends(get_request_id)],
) -> MarketoSuccessResponse:
    """Create a new TSV activity export job."""
    response.headers["X-Request-Id"] = request_id
    result = create_export(db=db, request=request, request_id=request_id)
    return MarketoSuccessResponse(
        requestId=request_id,
        success=True,
        result=[result],
    )


@router.post(
    "/{exportId}/enqueue.json",
    response_model=MarketoSuccessResponse,
    summary="Enqueue activity export job",
    description="Enqueue a created export job for processing. Enforces active queue limits and schedules completion.",
)
def enqueue_export_job(
    exportId: str,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    current_token: Annotated[AccessToken, Depends(get_current_token)],
    request_id: Annotated[str, Depends(get_request_id)],
    x_mock_record_count: Annotated[int | None, Header(alias="X-Mock-Record-Count")] = None,
) -> MarketoSuccessResponse:
    """Enqueue an export job into the processing queue."""
    response.headers["X-Request-Id"] = request_id
    result = enqueue_export(
        db=db,
        export_id=exportId,
        request_id=request_id,
        mock_record_count=x_mock_record_count,
    )
    return MarketoSuccessResponse(
        requestId=request_id,
        success=True,
        result=[result],
    )


@router.get(
    "/{exportId}/status.json",
    response_model=MarketoSuccessResponse,
    summary="Get export job status",
    description="Check the current status (Created, Queued, Processing, Completed) of an export job.",
)
def poll_export_status(
    exportId: str,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    current_token: Annotated[AccessToken, Depends(get_current_token)],
    request_id: Annotated[str, Depends(get_request_id)],
) -> MarketoSuccessResponse:
    """Poll status of an export job."""
    response.headers["X-Request-Id"] = request_id
    result = get_export_status(db=db, export_id=exportId, request_id=request_id)
    return MarketoSuccessResponse(
        requestId=request_id,
        success=True,
        result=[result],
    )


@router.get(
    "/{exportId}/file.json",
    summary="Download generated export file",
    description="Download the generated TSV file. Successful response is a TSV file, even though the endpoint ends in file.json.",
    responses={
        200: {
            "content": {"text/tab-separated-values": {}},
            "description": "TSV file download for completed export job.",
        },
        204: {
            "description": "No content when export generated zero records (X-Mock-Record-Count: 0).",
        },
    },
)
def download_export_file(
    exportId: str,
    db: Annotated[Session, Depends(get_db)],
    current_token: Annotated[AccessToken, Depends(get_current_token)],
    request_id: Annotated[str, Depends(get_request_id)],
) -> RawResponse:
    """Download the completed TSV export file."""
    file_result = get_export_file(db=db, export_id=exportId, request_id=request_id)

    if file_result.is_empty:
        # HTTP 204 No Content for zero-record mock
        headers = {
            "X-Export-Id": file_result.export_id,
            "X-Number-Of-Days": str(file_result.number_of_days),
            "X-Record-Count": "0",
            "X-Request-Id": request_id,
        }
        return RawResponse(status_code=204, headers=headers)

    headers = {
        "Content-Type": "text/tab-separated-values; charset=utf-8",
        "Content-Disposition": f'attachment; filename="marketo_fillout_form_{file_result.export_id}.tsv"',
        "X-Export-Id": file_result.export_id,
        "X-Number-Of-Days": str(file_result.number_of_days),
        "X-Record-Count": str(file_result.number_of_records),
        "X-Checksum-SHA256": file_result.checksum_hex,
        "X-Request-Id": request_id,
        "Cache-Control": "no-store",
    }
    return RawResponse(
        content=file_result.file_bytes,
        status_code=200,
        headers=headers,
        media_type="text/tab-separated-values; charset=utf-8",
    )
