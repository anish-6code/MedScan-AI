"""
app/routers/vitals.py

POST   /vitals/{patient_id}         — ingest a reading
GET    /vitals/{patient_id}         — paginated history (filterable by ?start=&end=)
GET    /vitals/{patient_id}/latest  — snapshot for dashboard cards
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud.vitals import create_reading, get_latest, get_readings
from app.crud.patient import get_patient_by_id
from app.dependencies import get_current_doctor, get_db
from app.models.user import User
from app.schemas.vitals import VitalsCreate, VitalsPage, VitalsRead

router = APIRouter(prefix="/vitals", tags=["vitals"])


def _check_patient(db: Session, patient_id: uuid.UUID):
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")
    return patient


@router.post(
    "/{patient_id}",
    response_model=VitalsRead,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a vitals reading",
)
def ingest(
    patient_id: uuid.UUID,
    payload: VitalsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    """
    Accepts a single vitals reading for a patient.
    Source tag distinguishes manual entry from simulator / IoT device.
    Automatically triggers rule engine check via Celery after insertion.
    """
    _check_patient(db, patient_id)
    reading = create_reading(db, patient_id=patient_id, payload=payload)

    # Fire rule engine asynchronously
    try:
        from app.tasks.tasks_vitals import check_vitals_rules
        check_vitals_rules.delay(str(reading.id))
    except Exception:
        pass  # Don't fail ingestion if Celery is unavailable

    return reading


@router.get(
    "/{patient_id}/latest",
    response_model=VitalsRead | None,
    summary="Latest vitals snapshot for a patient",
)
def latest(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    _check_patient(db, patient_id)
    return get_latest(db, patient_id)


@router.get(
    "/{patient_id}",
    response_model=VitalsPage,
    summary="Paginated vitals history for a patient",
)
def history(
    patient_id: uuid.UUID,
    start: datetime | None = Query(None, description="ISO 8601 start datetime"),
    end:   datetime | None = Query(None, description="ISO 8601 end datetime"),
    page:  int = Query(1, ge=1),
    size:  int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    _check_patient(db, patient_id)
    total, items = get_readings(db, patient_id, start=start, end=end, page=page, size=size)
    return VitalsPage(total=total, page=page, size=size, results=items)
