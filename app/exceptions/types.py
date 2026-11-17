"""Custom exception types for Marketo-style error handling."""

from __future__ import annotations


class MarketoAPIError(Exception):
    """Base exception for all Marketo-style API errors."""

    def __init__(self, status_code: int, error_code: str, message: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(message)


class InvalidTokenError(MarketoAPIError):
    """Raised when the access token is invalid, missing, expired, or revoked."""

    def __init__(self, message: str = "Access token invalid") -> None:
        super().__init__(status_code=401, error_code="601", message=message)


class ExportNotFoundError(MarketoAPIError):
    """Raised when the requested export job does not exist."""

    def __init__(self, export_id: str = "") -> None:
        msg = f"Export job not found: {export_id}" if export_id else "Export job not found"
        super().__init__(status_code=404, error_code="1034", message=msg)


class InvalidExportStateError(MarketoAPIError):
    """Raised when the export job is not in the required state."""

    def __init__(self, message: str = "Export job has already been enqueued") -> None:
        super().__init__(status_code=409, error_code="1035", message=message)


class TooManyJobsError(MarketoAPIError):
    """Raised when the active-job limit is reached."""

    def __init__(self) -> None:
        super().__init__(
            status_code=422, error_code="1029", message="Too many jobs in queue"
        )


class InvalidDateRangeError(MarketoAPIError):
    """Raised when the date range is invalid."""

    def __init__(self, message: str = "Invalid date range") -> None:
        super().__init__(status_code=422, error_code="1003", message=message)


class UnsupportedActivityError(MarketoAPIError):
    """Raised for unsupported activity type IDs."""

    def __init__(self, message: str = "Unsupported activity type") -> None:
        super().__init__(status_code=422, error_code="1005", message=message)


class ExportNotReadyError(MarketoAPIError):
    """Raised when the export file is requested before completion."""

    def __init__(self) -> None:
        super().__init__(
            status_code=409,
            error_code="1036",
            message="Export file is not available because the job is not Completed",
        )


class ExportReconciliationError(MarketoAPIError):
    """Raised when generated TSV does not match persisted checksum/size."""

    def __init__(self, message: str = "Export generation or reconciliation failed") -> None:
        super().__init__(status_code=500, error_code="1037", message=message)


class MaxRecordsExceededError(MarketoAPIError):
    """Raised when the calculated record count exceeds the maximum."""

    def __init__(self, total: int, maximum: int) -> None:
        super().__init__(
            status_code=422,
            error_code="1041",
            message=f"Export exceeds maximum record count: {total} > {maximum}",
        )


class InvalidRequestError(MarketoAPIError):
    """Raised for general request validation errors."""

    def __init__(self, message: str = "Invalid request") -> None:
        super().__init__(status_code=422, error_code="1040", message=message)
