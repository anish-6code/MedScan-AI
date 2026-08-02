import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class VitalsCreate(BaseModel):
    source:           str   = "manual"
    heart_rate:       float | None = Field(None, ge=0, le=400,  description="bpm")
    spo2:             float | None = Field(None, ge=0, le=100,  description="%")
    systolic_bp:      float | None = Field(None, ge=0, le=300,  description="mmHg")
    diastolic_bp:     float | None = Field(None, ge=0, le=200,  description="mmHg")
    temperature:      float | None = Field(None, ge=25, le=45,  description="°C")
    respiratory_rate: float | None = Field(None, ge=0, le=100,  description="breaths/min")
    notes:            str   | None = None


class VitalsRead(BaseModel):
    model_config = {"from_attributes": True}

    id:               uuid.UUID
    patient_id:       uuid.UUID
    recorded_at:      datetime
    source:           str
    heart_rate:       float | None
    spo2:             float | None
    systolic_bp:      float | None
    diastolic_bp:     float | None
    temperature:      float | None
    respiratory_rate: float | None
    notes:            str | None


class VitalsPage(BaseModel):
    total:   int
    page:    int
    size:    int
    results: list[VitalsRead]
