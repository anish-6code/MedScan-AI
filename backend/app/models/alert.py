"""
app/models/alert_rule.py + app/models/alert.py combined in one file for Module 9.

AlertRule — per-vital threshold with optional patient scope and breach counter.
Alert     — triggered event, severity, status, acknowledged_by audit.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VitalSignEnum(str, enum.Enum):
    heart_rate       = "heart_rate"
    spo2             = "spo2"
    systolic_bp      = "systolic_bp"
    diastolic_bp     = "diastolic_bp"
    temperature      = "temperature"
    respiratory_rate = "respiratory_rate"


class AlertSeverity(str, enum.Enum):
    low      = "low"
    moderate = "moderate"
    critical = "critical"


class AlertStatus(str, enum.Enum):
    active       = "active"
    acknowledged = "acknowledged"
    resolved     = "resolved"


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"), default=uuid.uuid4,
    )
    # NULL patient_id = global default rule
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=True,
    )
    vital_sign:  Mapped[VitalSignEnum]  = mapped_column(Enum(VitalSignEnum,  name="vital_sign_enum"),  nullable=False)
    min_value:   Mapped[float | None]   = mapped_column(Float,   nullable=True)
    max_value:   Mapped[float | None]   = mapped_column(Float,   nullable=True)
    severity:    Mapped[AlertSeverity]  = mapped_column(Enum(AlertSeverity,  name="alert_severity_enum"), nullable=False, default=AlertSeverity.moderate)
    consecutive_breaches_required: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active:   Mapped[bool]           = mapped_column(Boolean, nullable=False, default=True)
    created_at:  Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient   = relationship("Patient", foreign_keys=[patient_id])
    alerts    = relationship("Alert", back_populates="rule", cascade="all, delete-orphan")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"), default=uuid.uuid4,
    )
    patient_id:  Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False,
    )
    rule_id:    Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True,
    )
    reading_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vitals_readings.id", ondelete="SET NULL"), nullable=True,
    )
    vital_sign:  Mapped[VitalSignEnum]  = mapped_column(Enum(VitalSignEnum,  name="vital_sign_enum"), nullable=False)
    value:       Mapped[float]          = mapped_column(Float, nullable=False)
    severity:    Mapped[AlertSeverity]  = mapped_column(Enum(AlertSeverity,  name="alert_severity_enum"), nullable=False)
    status:      Mapped[AlertStatus]    = mapped_column(Enum(AlertStatus,    name="alert_status_enum"),  nullable=False, default=AlertStatus.active)
    message:     Mapped[str | None]     = mapped_column(Text, nullable=True)
    triggered_at:    Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )

    patient     = relationship("Patient",    foreign_keys=[patient_id])
    rule        = relationship("AlertRule",  back_populates="alerts")
    reading     = relationship("VitalsReading", foreign_keys=[reading_id])
    acknowledger= relationship("User",       foreign_keys=[acknowledged_by])

    def __repr__(self) -> str:
        return f"<Alert {self.vital_sign}={self.value} sev={self.severity} status={self.status}>"
