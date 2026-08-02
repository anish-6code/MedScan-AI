import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DoctorCorrection(Base):
    __tablename__ = "doctor_corrections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"), default=uuid.uuid4,
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    corrected_findings:   Mapped[dict | None]  = mapped_column(JSONB,  nullable=True)
    doctor_notes:         Mapped[str | None]   = mapped_column(Text,   nullable=True)
    override_confidence:  Mapped[float | None] = mapped_column(Float,  nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    scan   = relationship("Scan", foreign_keys=[scan_id])
    doctor = relationship("User", foreign_keys=[doctor_id])

    def __repr__(self) -> str:
        return f"<DoctorCorrection scan={self.scan_id} doctor={self.doctor_id}>"
