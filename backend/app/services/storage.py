"""
app/services/storage.py

Dual-backend file storage:
  - STORAGE_BACKEND=local  → save to UPLOAD_DIR on disk (default / dev)
  - STORAGE_BACKEND=s3     → upload to S3_BUCKET_NAME

Both return the stored path/key as a string that gets persisted in scans.file_path.
"""
import io
import os
import uuid

import pydicom
from fastapi import HTTPException, status

from app.config import settings


# ── DICOM validation ───────────────────────────────────────────────────────────

# DICOM files have the magic string "DICM" at byte offset 128
_DICOM_MAGIC_OFFSET = 128
_DICOM_MAGIC = b"DICM"


def validate_dicom(data: bytes) -> None:
    """
    Raises HTTP 422 if the bytes are not a valid DICOM file.
    Checks both magic bytes and attempts pydicom parse for extra safety.
    """
    # 1. Magic bytes check (fast)
    has_magic = (
        len(data) > _DICOM_MAGIC_OFFSET + 4
        and data[_DICOM_MAGIC_OFFSET : _DICOM_MAGIC_OFFSET + 4] == _DICOM_MAGIC
    )

    # 2. pydicom parse check (handles some valid DICOMs without the preamble)
    dicom_parseable = False
    try:
        pydicom.dcmread(io.BytesIO(data), stop_before_pixels=True, force=False)
        dicom_parseable = True
    except Exception:
        pass

    if not has_magic and not dicom_parseable:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File is not a valid DICOM file.",
        )


# ── Storage backends ───────────────────────────────────────────────────────────

def _save_local(patient_id: uuid.UUID, scan_id: uuid.UUID, data: bytes) -> str:
    """Save file to local disk. Returns relative path stored in DB."""
    folder = os.path.join(settings.UPLOAD_DIR, str(patient_id))
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{scan_id}.dcm")
    with open(filepath, "wb") as f:
        f.write(data)
    return filepath


def _save_s3(patient_id: uuid.UUID, scan_id: uuid.UUID, data: bytes) -> str:
    """Upload file to S3. Returns s3 key stored in DB."""
    import boto3
    s3_key = f"scans/{patient_id}/{scan_id}.dcm"
    client = boto3.client(
        "s3",
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    client.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=s3_key,
        Body=data,
        ContentType="application/dicom",
    )
    return s3_key


def save_file(patient_id: uuid.UUID, scan_id: uuid.UUID, data: bytes) -> str:
    """
    Dispatch to the configured storage backend.
    Returns the stored path/key to be persisted in scans.file_path.
    """
    if settings.STORAGE_BACKEND == "s3":
        return _save_s3(patient_id, scan_id, data)
    return _save_local(patient_id, scan_id, data)
