import uuid
from datetime import datetime

from pydantic import BaseModel


class AlertRuleCreate(BaseModel):
    patient_id:  uuid.UUID | None = None
    vital_sign:  str
    min_value:   float | None = None
    max_value:   float | None = None
    severity:    str = "moderate"
    consecutive_breaches_required: int = 1


class AlertRuleRead(BaseModel):
    model_config = {"from_attributes": True}
    id:          uuid.UUID
    patient_id:  uuid.UUID | None
    vital_sign:  str
    min_value:   float | None
    max_value:   float | None
    severity:    str
    consecutive_breaches_required: int
    is_active:   bool
    created_at:  datetime


class AlertRead(BaseModel):
    model_config = {"from_attributes": True}
    id:            uuid.UUID
    patient_id:    uuid.UUID
    rule_id:       uuid.UUID | None
    reading_id:    uuid.UUID | None
    vital_sign:    str
    value:         float
    severity:      str
    status:        str
    message:       str | None
    triggered_at:  datetime
    acknowledged_at: datetime | None
    acknowledged_by: uuid.UUID | None


class AlertAcknowledge(BaseModel):
    """Body for PATCH /alerts/{id}/acknowledge"""
    pass  # body is empty — actor comes from JWT
