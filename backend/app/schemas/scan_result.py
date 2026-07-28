import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ScanResultRead(BaseModel):
    model_config = {"from_attributes": True}

    id:               uuid.UUID
    scan_id:          uuid.UUID
    mask_path:        str | None
    overlay_path:     str | None
    confidence_score: float | None
    findings_json:    dict[str, Any] | None
    created_at:       datetime
