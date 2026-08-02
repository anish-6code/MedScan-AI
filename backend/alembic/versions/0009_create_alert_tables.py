"""
Module 9: Alert Rule Engine
Migration 0009 — creates alert_rules and alerts tables

Revision ID: 0009_create_alert_tables
Revises: 0008_create_vitals_readings
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0009_create_alert_tables"
down_revision: Union[str, None] = "0008_create_vitals_readings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VITAL_ENUM = postgresql.ENUM(
    "heart_rate","spo2","systolic_bp","diastolic_bp","temperature","respiratory_rate",
    name="vital_sign_enum", create_type=False,
)
SEVERITY_ENUM = postgresql.ENUM("low","moderate","critical", name="alert_severity_enum", create_type=False)
ALERT_STATUS_ENUM = postgresql.ENUM("active","acknowledged","resolved", name="alert_status_enum", create_type=False)


def upgrade() -> None:
    op.execute("CREATE TYPE IF NOT EXISTS vital_sign_enum AS ENUM ('heart_rate','spo2','systolic_bp','diastolic_bp','temperature','respiratory_rate')")
    op.execute("CREATE TYPE IF NOT EXISTS alert_severity_enum AS ENUM ('low','moderate','critical')")
    op.execute("CREATE TYPE IF NOT EXISTS alert_status_enum AS ENUM ('active','acknowledged','resolved')")

    # alert_rules
    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("patient_id",    postgresql.UUID(as_uuid=True), nullable=True),   # NULL = global default
        sa.Column("vital_sign",    VITAL_ENUM,     nullable=False),
        sa.Column("min_value",     sa.Float(),     nullable=True),
        sa.Column("max_value",     sa.Float(),     nullable=True),
        sa.Column("severity",      SEVERITY_ENUM,  nullable=False, server_default="moderate"),
        sa.Column("consecutive_breaches_required", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active",     sa.Boolean(),   nullable=False, server_default="true"),
        sa.Column("created_at",    sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alert_rules_patient_vital", "alert_rules", ["patient_id", "vital_sign"])

    # alerts
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("patient_id",   postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_id",      postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reading_id",   postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("vital_sign",   VITAL_ENUM,    nullable=False),
        sa.Column("value",        sa.Float(),    nullable=False),
        sa.Column("severity",     SEVERITY_ENUM, nullable=False),
        sa.Column("status",       ALERT_STATUS_ENUM, nullable=False, server_default="active"),
        sa.Column("message",      sa.Text(),     nullable=True),
        sa.Column("triggered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"],   ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"],      ["alert_rules.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reading_id"],   ["vitals_readings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["acknowledged_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_patient_status", "alerts", ["patient_id", "status"])
    op.create_index("ix_alerts_triggered_at",   "alerts", ["triggered_at"])


def downgrade() -> None:
    op.drop_index("ix_alerts_triggered_at",    table_name="alerts")
    op.drop_index("ix_alerts_patient_status",  table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("ix_alert_rules_patient_vital", table_name="alert_rules")
    op.drop_table("alert_rules")
    op.execute("DROP TYPE IF EXISTS vital_sign_enum")
    op.execute("DROP TYPE IF EXISTS alert_severity_enum")
    op.execute("DROP TYPE IF EXISTS alert_status_enum")
