"""Alembic migration: create scans table

Revision ID: 0003_create_scans
Revises: 0002_create_patients
Create Date: 2026-07-29
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003_create_scans"
down_revision: Union[str, None] = "0002_create_patients"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    scan_status_enum = sa.Enum(
        "uploaded", "processing", "done", "failed",
        name="scan_status_enum",
    )
    scan_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "scans",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("patient_id",  postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("file_path",         sa.String(),         nullable=False),
        sa.Column("original_filename", sa.String(255),      nullable=False),
        sa.Column("content_type",      sa.String(100),      nullable=False),
        sa.Column("file_size_bytes",   sa.BigInteger(),     nullable=False),
        sa.Column(
            "status",
            sa.Enum("uploaded", "processing", "done", "failed", name="scan_status_enum"),
            server_default="uploaded",
            nullable=False,
        ),
        sa.Column(
            "upload_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["patient_id"],  ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"],    ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scans_patient_id",  "scans", ["patient_id"])
    op.create_index("ix_scans_uploaded_by", "scans", ["uploaded_by"])


def downgrade() -> None:
    op.drop_index("ix_scans_uploaded_by", table_name="scans")
    op.drop_index("ix_scans_patient_id",  table_name="scans")
    op.drop_table("scans")
    sa.Enum(name="scan_status_enum").drop(op.get_bind(), checkfirst=True)
