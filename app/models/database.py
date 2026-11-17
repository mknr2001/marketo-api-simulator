"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, Text, TypeDecorator, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class SafeBigInteger(TypeDecorator):
    """Stores full 64-bit unsigned integers safely across SQLite and PostgreSQL."""

    impl = BigInteger
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(32))
        return dialect.type_descriptor(BigInteger())

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if dialect.name == "sqlite":
            return str(value)
        return int(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        return int(value)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


class AccessToken(Base):
    """Stores hashed access tokens."""

    __tablename__ = "access_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    client_id: Mapped[str] = mapped_column(String(256), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_access_tokens_token_hash", "token_hash"),
        Index("ix_access_tokens_expires_at", "expires_at"),
    )


class ExportJob(Base):
    """Stores export job metadata and state."""

    __tablename__ = "export_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    export_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    request_id: Mapped[str] = mapped_column(String(256), nullable=False)
    activity_type_ids: Mapped[str] = mapped_column(String(256), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    number_of_days: Mapped[int] = mapped_column(Integer, nullable=False)
    output_format: Mapped[str] = mapped_column(String(10), nullable=False, default="TSV")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Created")
    deterministic_seed: Mapped[int | None] = mapped_column(SafeBigInteger, nullable=True)
    daily_record_counts_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    number_of_records: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    file_checksum_sha256: Mapped[str | None] = mapped_column(String(256), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_export_jobs_export_id", "export_id"),
        Index("ix_export_jobs_status", "status"),
        Index("ix_export_jobs_created_at", "created_at"),
    )
