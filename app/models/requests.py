"""Pydantic v2 request models with strict validation."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class CreatedAtFilter(BaseModel):
    """Date range filter for the export request."""

    model_config = ConfigDict(extra="forbid")

    startAt: datetime
    endAt: datetime

    @field_validator("startAt", "endAt")
    @classmethod
    def must_have_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("Timestamp must include timezone information")
        return v.astimezone(UTC)


class ExportFilter(BaseModel):
    """Top-level filter for the create-export request."""

    model_config = ConfigDict(extra="forbid")

    createdAt: CreatedAtFilter
    activityTypeIds: list[int]

    @field_validator("activityTypeIds")
    @classmethod
    def validate_activity_type_ids(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("activityTypeIds must not be empty")
        if len(v) != 1:
            raise ValueError("activityTypeIds must contain exactly one value")
        if v[0] != 2:
            raise ValueError(
                f"Unsupported activity type ID: {v[0]}. Only activity type 2 (Fill Out Form) is supported"
            )
        return v


class CreateExportRequest(BaseModel):
    """Request body for POST /bulk/v1/activities/export/create.json."""

    model_config = ConfigDict(extra="forbid")

    filter: ExportFilter

    @model_validator(mode="after")
    def validate_date_range(self) -> CreateExportRequest:
        start = self.filter.createdAt.startAt
        end = self.filter.createdAt.endAt
        if start >= end:
            raise ValueError("startAt must be strictly earlier than endAt")
        return self
