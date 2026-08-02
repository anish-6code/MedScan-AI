import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.vitals import VitalsReading
from app.schemas.vitals import VitalsCreate


def create_reading(
    db: Session, *, patient_id: uuid.UUID, payload: VitalsCreate
) -> VitalsReading:
    reading = VitalsReading(patient_id=patient_id, **payload.model_dump())
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def get_readings(
    db: Session,
    patient_id: uuid.UUID,
    *,
    start: datetime | None = None,
    end:   datetime | None = None,
    page:  int = 1,
    size:  int = 50,
) -> tuple[int, list[VitalsReading]]:
    q = db.query(VitalsReading).filter(VitalsReading.patient_id == patient_id)
    if start:
        q = q.filter(VitalsReading.recorded_at >= start)
    if end:
        q = q.filter(VitalsReading.recorded_at <= end)
    total  = q.count()
    items  = q.order_by(VitalsReading.recorded_at.desc())\
               .offset((page - 1) * size).limit(size).all()
    return total, items


def get_latest(db: Session, patient_id: uuid.UUID) -> VitalsReading | None:
    return (
        db.query(VitalsReading)
        .filter(VitalsReading.patient_id == patient_id)
        .order_by(VitalsReading.recorded_at.desc())
        .first()
    )
