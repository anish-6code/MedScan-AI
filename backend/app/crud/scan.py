import uuid

from sqlalchemy.orm import Session

from app.models.scan import Scan


def create_scan(
    db: Session,
    *,
    scan_id: uuid.UUID | None = None,
    patient_id: uuid.UUID,
    uploaded_by: uuid.UUID | None,
    file_path: str,
    original_filename: str,
    content_type: str,
    file_size_bytes: int,
) -> Scan:
    scan = Scan(
        id=scan_id or uuid.uuid4(),
        patient_id=patient_id,
        uploaded_by=uploaded_by,
        file_path=file_path,
        original_filename=original_filename,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        status="uploaded",
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan



def get_scan_by_id(db: Session, scan_id: uuid.UUID) -> Scan | None:
    return db.query(Scan).filter(Scan.id == scan_id).first()


def update_scan_status(db: Session, scan_id: uuid.UUID, status: str) -> Scan | None:
    """Update a scan's status field and commit. Returns updated scan or None."""
    scan = get_scan_by_id(db, scan_id)
    if scan:
        scan.status = status
        db.commit()
        db.refresh(scan)
    return scan

