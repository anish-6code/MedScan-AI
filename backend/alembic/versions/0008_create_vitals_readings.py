"""Alembic migration: create vitals_readings table

Revision ID: 0008_create_vitals_readings
Revises: 0007_create_doctor_corrections
Create Date: 2026-08-03

TimescaleDB-ready: add hypertable call if TimescaleDB extension is available.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0008_create_vitals_readings"
down_revision: Union[str, None] = "0007_create_doctor_corrections"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vitals_readings",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("patient_id",     postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recorded_at",    sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("source",         sa.String(64),  nullable=False, server_default="manual"),
        # Vital signs (all nullable — not every reading has every value)
        sa.Column("heart_rate",      sa.Float(), nullable=True),   # bpm
        sa.Column("spo2",            sa.Float(), nullable=True),   # %
        sa.Column("systolic_bp",     sa.Float(), nullable=True),   # mmHg
        sa.Column("diastolic_bp",    sa.Float(), nullable=True),   # mmHg
        sa.Column("temperature",     sa.Float(), nullable=True),   # °C
        sa.Column("respiratory_rate",sa.Float(), nullable=True),   # breaths/min
        sa.Column("notes",           sa.Text(),  nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vitals_patient_time", "vitals_readings",
                    ["patient_id", "recorded_at"])

    # TimescaleDB hypertable (gracefully skipped on plain Postgres)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
            ) THEN
                PERFORM create_hypertable(
                    'vitals_readings', 'recorded_at',
                    if_not_exists => TRUE
                );
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.drop_index("ix_vitals_patient_time", table_name="vitals_readings")
    op.drop_table("vitals_readings")
