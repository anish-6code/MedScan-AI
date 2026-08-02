"""Alembic migration: create doctor_corrections table

Revision ID: 0007_create_doctor_corrections
Revises: 0006_add_report_path
Create Date: 2026-08-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0007_create_doctor_corrections"
down_revision: Union[str, None] = "0006_add_report_path"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "doctor_corrections",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("scan_id",       postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doctor_id",     postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("corrected_findings", postgresql.JSONB(), nullable=True),
        sa.Column("doctor_notes",  sa.Text(), nullable=True),
        sa.Column("override_confidence", sa.Float(), nullable=True),
        sa.Column("created_at",    sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["scan_id"],   ["scans.id"],   ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["doctor_id"], ["users.id"],   ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doctor_corrections_scan_id", "doctor_corrections", ["scan_id"])


def downgrade() -> None:
    op.drop_index("ix_doctor_corrections_scan_id", table_name="doctor_corrections")
    op.drop_table("doctor_corrections")
