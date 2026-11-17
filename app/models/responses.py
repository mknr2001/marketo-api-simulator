"""Pydantic v2 response models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MarketoError(BaseModel):
    """Single error in a Marketo-style error response."""

    code: str
    message: str


class MarketoErrorResponse(BaseModel):
    """Standard Marketo-style error response."""

    requestId: str
    success: bool = False
    errors: list[MarketoError]


class TokenResponse(BaseModel):
    """Response from the access-token endpoint."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str = "marketo.mock.api"


class ExportJobResult(BaseModel):
    """Single export-job result element."""

    model_config = ConfigDict(populate_by_name=True)

    exportId: str
    status: str
    createdAt: str
    queuedAt: str | None = None
    startedAt: str | None = None
    finishedAt: str | None = None
    format: str = "TSV"
    numberOfDays: int | None = None
    numberOfRecords: int | None = None
    fileSize: int | None = None
    fileChecksum: str | None = None


class MarketoSuccessResponse(BaseModel):
    """Standard Marketo-style success response."""

    requestId: str
    success: bool = True
    result: list[ExportJobResult]
