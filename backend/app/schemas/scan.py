import uuid
from datetime import datetime

from pydantic import BaseModel


class ScanRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    patient_id: uuid.UUID
    uploaded_by: uuid.UUID | None
    file_path: str
    original_filename: str
    content_type: str
    file_size_bytes: int
    status: str
    upload_time: datetime


class ScanUploadResponse(BaseModel):
    """Returned immediately after a successful upload — before any AI processing."""
    id: uuid.UUID
    patient_id: uuid.UUID
    status: str
    file_path: str
    original_filename: str
    file_size_bytes: int
    upload_time: datetime
