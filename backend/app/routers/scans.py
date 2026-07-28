import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.crud.patient import get_patient_by_id
from app.crud.scan import create_scan, get_scan_by_id
from app.dependencies import get_current_doctor, get_db
from app.models.user import User
from app.schemas.scan import ScanRead, ScanUploadResponse
from app.services.storage import save_file, validate_dicom

router = APIRouter(prefix="/scans", tags=["scans"])


# ── POST /scans/upload ─────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=ScanUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a DICOM scan file",
)
async def upload_scan(
    patient_id: uuid.UUID = Form(..., description="UUID of the patient this scan belongs to"),
    file: UploadFile = File(..., description="DICOM file (.dcm)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    """
    Accepts a multipart DICOM file upload.

    1. Validates the patient exists (404 if not)
    2. Validates the file is a real DICOM (422 if not)
    3. Saves file to storage backend (local or S3)
    4. Persists scan metadata in Postgres with status = `uploaded`
    5. Returns scan_id + status immediately — AI processing happens async later
    """
    # 1. Patient must exist
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found.",
        )

    # 2. Read file bytes (FastAPI streams it in memory for small files)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    # 3. DICOM validation (raises 422 internally if invalid)
    validate_dicom(file_bytes)

    # 4. Allocate scan_id now so storage path and DB row are in sync
    scan_id = uuid.uuid4()

    # 5. Save to storage backend (local or S3)
    stored_path = save_file(
        patient_id=patient_id,
        scan_id=scan_id,
        data=file_bytes,
    )

    # 6. Persist metadata row — status defaults to "uploaded"
    scan = create_scan(
        db,
        scan_id=scan_id,
        patient_id=patient_id,
        uploaded_by=current_user.id,
        file_path=stored_path,
        original_filename=file.filename or f"{scan_id}.dcm",
        content_type=file.content_type or "application/dicom",
        file_size_bytes=len(file_bytes),
    )

    return scan



# ── GET /scans/{scan_id} ───────────────────────────────────────────────────────

@router.get(
    "/{scan_id}",
    response_model=ScanRead,
    summary="Get scan metadata",
)
def read_scan(
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    scan = get_scan_by_id(db, scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found.",
        )
    return scan
