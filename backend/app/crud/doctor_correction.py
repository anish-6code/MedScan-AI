import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.doctor_correction import DoctorCorrection


def create_correction(
    db: Session,
    *,
    scan_id: uuid.UUID,
    doctor_id: uuid.UUID | None,
    corrected_findings: dict[str, Any] | None = None,
    doctor_notes: str | None = None,
    override_confidence: float | None = None,
) -> DoctorCorrection:
    correction = DoctorCorrection(
        scan_id=scan_id,
        doctor_id=doctor_id,
        corrected_findings=corrected_findings,
        doctor_notes=doctor_notes,
        override_confidence=override_confidence,
    )
    db.add(correction)
    db.commit()
    db.refresh(correction)
    return correction


def get_corrections_by_scan(db: Session, scan_id: uuid.UUID) -> list[DoctorCorrection]:
    return (
        db.query(DoctorCorrection)
        .filter(DoctorCorrection.scan_id == scan_id)
        .order_by(DoctorCorrection.created_at.desc())
        .all()
    )
