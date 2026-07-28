"""Add preprocessed to scan_status_enum

Revision ID: 0004_add_preprocessed_status
Revises: 0003_create_scans
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004_add_preprocessed_status"
down_revision: Union[str, None] = "0003_create_scans"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL requires ALTER TYPE to add enum values
    op.execute("ALTER TYPE scan_status_enum ADD VALUE IF NOT EXISTS 'preprocessed'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values without recreation.
    # Downgrade is a no-op — guard by not using 'preprocessed' in old code.
    pass
