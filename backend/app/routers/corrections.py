"""
app/routers/corrections.py

PATCH /scans/{scan_id}/result  — Doctor saves corrections/notes
GET   /scans/{scan_id}/corrections — List all corrections for a scan
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.doctor_correction import create_correction, get_corrections_by_scan
from app.crud.scan import get_scan_by_id
from app.dependencies import get_current_doctor, get_db
from app.models.user import User
from app.schemas.doctor_correction import DoctorCorrectionCreate, DoctorCorrectionRead

router = APIRouter(prefix="/scans", tags=["corrections"])


@router.patch(
    "/{scan_id}/result",
    response_model=DoctorCorrectionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Save doctor corrections to AI result",
)
def save_correction(
    scan_id: uuid.UUID,
    payload: DoctorCorrectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    """
    Doctors can override AI findings without mutating the original result.
    Each PATCH creates a new correction record — full audit trail preserved.
    """
    scan = get_scan_by_id(db, scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Scan {scan_id} not found.")
    return create_correction(
        db,
        scan_id=scan_id,
        doctor_id=current_user.id,
        corrected_findings=payload.corrected_findings,
        doctor_notes=payload.doctor_notes,
        override_confidence=payload.override_confidence,
    )


@router.get(
    "/{scan_id}/corrections",
    response_model=list[DoctorCorrectionRead],
    summary="List all doctor corrections for a scan",
)
def list_corrections(
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    return get_corrections_by_scan(db, scan_id)
