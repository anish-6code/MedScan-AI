import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.patient import create_patient, get_patient_by_id
from app.dependencies import get_current_doctor, get_db
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientRead, PatientSummary

router = APIRouter(prefix="/patients", tags=["patients"])


# ── POST /patients ─────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=PatientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new patient record",
)
def create(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    """
    Creates a patient and automatically assigns the authenticated doctor.
    Returns 409 if the MRN already exists.
    """
    return create_patient(db, payload, assigned_doctor_id=current_user.id)


# ── GET /patients/{patient_id} ─────────────────────────────────────────────────

@router.get(
    "/{patient_id}",
    response_model=PatientRead,
    summary="Get full patient profile",
)
def read(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found.",
        )
    return patient


# ── GET /patients/{patient_id}/summary ────────────────────────────────────────

@router.get(
    "/{patient_id}/summary",
    response_model=PatientSummary,
    summary="Get patient summary with scan/vital/alert stubs",
)
def summary(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    """
    Returns the patient's full profile plus stub arrays for:
    - scans   (populated by Module 3: Scan Ingestion)
    - vitals  (populated by Module 4: Vitals Monitoring)
    - alerts  (populated by Module 5: AI Alerts)
    """
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found.",
        )
    # Build summary: patient fields + empty stub arrays
    return PatientSummary(
        id=patient.id,
        mrn=patient.mrn,
        name=patient.name,
        date_of_birth=patient.date_of_birth,
        gender=patient.gender,
        admission_date=patient.admission_date,
        discharge_date=patient.discharge_date,
        assigned_doctor_id=patient.assigned_doctor_id,
        created_at=patient.created_at,
        scans=[],
        vitals=[],
        alerts=[],
    )
