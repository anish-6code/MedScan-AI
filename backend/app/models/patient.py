import uuid
from datetime import date, datetime

from sqlalchemy import DATE, DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    mrn: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(DATE, nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    admission_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    discharge_date: Mapped[date | None] = mapped_column(DATE, nullable=True)

    # FK to the doctor who owns this patient record
    assigned_doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship (lazy load — won't fetch unless accessed)
    assigned_doctor = relationship("User", foreign_keys=[assigned_doctor_id])

    def __repr__(self) -> str:
        return f"<Patient id={self.id} mrn={self.mrn} name={self.name}>"
