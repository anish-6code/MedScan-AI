import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    # ── Foreign keys ───────────────────────────────────────────────────────────
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── File metadata ──────────────────────────────────────────────────────────
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/dicom")
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # ── Status ─────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        Enum("uploaded", "processing", "done", "failed", name="scan_status_enum"),
        nullable=False,
        server_default="uploaded",
        default="uploaded",
    )

    upload_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    patient = relationship("Patient", foreign_keys=[patient_id])
    doctor  = relationship("User",    foreign_keys=[uploaded_by])

    def __repr__(self) -> str:
        return f"<Scan id={self.id} patient={self.patient_id} status={self.status}>"
