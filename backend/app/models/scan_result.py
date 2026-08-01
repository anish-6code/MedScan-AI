import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ScanResult(Base):
    __tablename__ = "scan_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )

    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,      # one result row per scan
        index=True,
    )

    # File paths
    mask_path:    Mapped[str | None] = mapped_column(String, nullable=True)
    overlay_path: Mapped[str | None] = mapped_column(String, nullable=True)
    report_path:  Mapped[str | None] = mapped_column(String, nullable=True)

    # AI scores
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Structured findings (JSONB for fast querying)
    findings_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship back to scan
    scan = relationship("Scan", foreign_keys=[scan_id])

    def __repr__(self) -> str:
        return f"<ScanResult scan={self.scan_id} confidence={self.confidence_score}>"
