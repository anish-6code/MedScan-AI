"""Add report_path to scan_results and create reports config

Revision ID: 0006_add_report_path
Revises: 0005_create_scan_results
Create Date: 2026-08-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_add_report_path"
down_revision: Union[str, None] = "0005_create_scan_results"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add report_path column to scan_results
    op.add_column(
        "scan_results",
        sa.Column("report_path", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scan_results", "report_path")
