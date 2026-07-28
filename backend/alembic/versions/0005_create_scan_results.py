"""Alembic migration: create scan_results table

Revision ID: 0005_create_scan_results
Revises: 0004_add_preprocessed_status
Create Date: 2026-07-29
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005_create_scan_results"
down_revision: Union[str, None] = "0004_add_preprocessed_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scan_results",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("scan_id",          postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mask_path",        sa.String(),   nullable=True),
        sa.Column("overlay_path",     sa.String(),   nullable=True),
        sa.Column("confidence_score", sa.Float(),    nullable=True),
        sa.Column("findings_json",    postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_id", name="uq_scan_results_scan_id"),
    )
    op.create_index("ix_scan_results_scan_id", "scan_results", ["scan_id"])


def downgrade() -> None:
    op.drop_index("ix_scan_results_scan_id", table_name="scan_results")
    op.drop_table("scan_results")
