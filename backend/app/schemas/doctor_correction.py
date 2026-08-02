import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DoctorCorrectionCreate(BaseModel):
    corrected_findings:  dict[str, Any] | None = None
    doctor_notes:        str | None = None
    override_confidence: float | None = None


class DoctorCorrectionRead(BaseModel):
    model_config = {"from_attributes": True}

    id:                  uuid.UUID
    scan_id:             uuid.UUID
    doctor_id:           uuid.UUID | None
    corrected_findings:  dict[str, Any] | None
    doctor_notes:        str | None
    override_confidence: float | None
    created_at:          datetime
