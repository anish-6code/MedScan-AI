import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Request schemas ────────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    mrn: str = Field(..., min_length=1, max_length=50, examples=["MRN-001"])
    name: str = Field(..., min_length=1, max_length=255, examples=["John Doe"])
    date_of_birth: date = Field(..., examples=["1985-06-15"])
    gender: str | None = Field(None, max_length=20, examples=["male"])
    admission_date: date | None = Field(None, examples=["2026-07-27"])
    discharge_date: date | None = Field(None, examples=[None])


# ── Response schemas ───────────────────────────────────────────────────────────

class PatientRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    mrn: str
    name: str
    date_of_birth: date
    gender: str | None
    admission_date: date | None
    discharge_date: date | None
    assigned_doctor_id: uuid.UUID | None
    created_at: datetime


class PatientSummary(PatientRead):
    """PatientRead extended with stub arrays for future modules."""
    scans: list[Any] = Field(default_factory=list)
    vitals: list[Any] = Field(default_factory=list)
    alerts: list[Any] = Field(default_factory=list)
