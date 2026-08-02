import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VitalsReading(Base):
    __tablename__ = "vitals_readings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"), default=uuid.uuid4,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")

    # Vital signs — all nullable
    heart_rate:       Mapped[float | None] = mapped_column(Float, nullable=True)
    spo2:             Mapped[float | None] = mapped_column(Float, nullable=True)
    systolic_bp:      Mapped[float | None] = mapped_column(Float, nullable=True)
    diastolic_bp:     Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature:      Mapped[float | None] = mapped_column(Float, nullable=True)
    respiratory_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes:            Mapped[str | None]   = mapped_column(Text, nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])

    def __repr__(self) -> str:
        return f"<VitalsReading patient={self.patient_id} at={self.recorded_at}>"
