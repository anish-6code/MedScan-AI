import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import PatientCreate


def get_patient_by_id(db: Session, patient_id: uuid.UUID) -> Patient | None:
    return db.query(Patient).filter(Patient.id == patient_id).first()


def get_patient_by_mrn(db: Session, mrn: str) -> Patient | None:
    return db.query(Patient).filter(Patient.mrn == mrn).first()


def create_patient(
    db: Session,
    data: PatientCreate,
    assigned_doctor_id: uuid.UUID | None = None,
) -> Patient:
    # Duplicate MRN guard
    if get_patient_by_mrn(db, data.mrn):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"MRN '{data.mrn}' is already registered.",
        )

    patient = Patient(
        mrn=data.mrn,
        name=data.name,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        admission_date=data.admission_date,
        discharge_date=data.discharge_date,
        assigned_doctor_id=assigned_doctor_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient
