"""Initial schema creation for access_tokens and export_jobs tables.

Revision ID: 001_initial_tables
Revises:
Create Date: 2026-11-16 00:00:00.000000

"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision: str = "001_initial_tables"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ── access_tokens ──────────────────────────────────────────
    op.create_table(
        "access_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("client_id", sa.String(length=256), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_access_tokens_token_hash", "access_tokens", ["token_hash"], unique=False)
    op.create_index("ix_access_tokens_expires_at", "access_tokens", ["expires_at"], unique=False)

    # ── export_jobs ────────────────────────────────────────────
    op.create_table(
        "export_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("export_id", sa.String(length=36), nullable=False),
        sa.Column("request_id", sa.String(length=256), nullable=False),
        sa.Column("activity_type_ids", sa.String(length=256), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("number_of_days", sa.Integer(), nullable=False),
        sa.Column("output_format", sa.String(length=10), server_default="TSV", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="Created", nullable=False),
        sa.Column("deterministic_seed", sa.BigInteger(), nullable=True),
        sa.Column("daily_record_counts_json", sa.Text(), nullable=True),
        sa.Column("number_of_records", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("file_checksum_sha256", sa.String(length=256), nullable=True),
        sa.Column("error_code", sa.String(length=10), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("export_id"),
    )
    op.create_index("ix_export_jobs_export_id", "export_jobs", ["export_id"], unique=True)
    op.create_index("ix_export_jobs_status", "export_jobs", ["status"], unique=False)
    op.create_index("ix_export_jobs_created_at", "export_jobs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_export_jobs_created_at", table_name="export_jobs")
    op.drop_index("ix_export_jobs_status", table_name="export_jobs")
    op.drop_index("ix_export_jobs_export_id", table_name="export_jobs")
    op.drop_table("export_jobs")

    op.drop_index("ix_access_tokens_expires_at", table_name="access_tokens")
    op.drop_index("ix_access_tokens_token_hash", table_name="access_tokens")
    op.drop_table("access_tokens")
