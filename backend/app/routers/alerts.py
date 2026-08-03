"""
app/routers/alerts.py

GET    /alerts                  — list alerts (filterable by patient, status)
PATCH  /alerts/{id}/acknowledge — acknowledge an active alert
POST   /alert-rules             — create a threshold rule
GET    /alert-rules             — list active rules
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud.alert import acknowledge_alert, create_rule, list_alerts, list_rules
from app.dependencies import get_current_doctor, get_db
from app.models.user import User
from app.schemas.alert import AlertAcknowledge, AlertRead, AlertRuleCreate, AlertRuleRead

router = APIRouter(tags=["alerts"])


# ── Alerts ────────────────────────────────────────────────────────────────────

@router.get(
    "/alerts",
    response_model=list[AlertRead],
    summary="List alerts (optionally filter by patient and/or status)",
)
def get_alerts(
    patient_id: uuid.UUID | None = Query(None),
    status_filter: str | None    = Query(None, alias="status",
                                          description="active | acknowledged | resolved"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    _, items = list_alerts(db, patient_id=patient_id, status=status_filter,
                            page=page, size=size)
    return items


@router.patch(
    "/alerts/{alert_id}/acknowledge",
    response_model=AlertRead,
    summary="Acknowledge an active alert",
)
def ack_alert(
    alert_id: uuid.UUID,
    _: AlertAcknowledge = AlertAcknowledge(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    alert = acknowledge_alert(db, alert_id, current_user.id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Alert {alert_id} not found.")
    return alert


# ── Alert Rules ───────────────────────────────────────────────────────────────

@router.post(
    "/alert-rules",
    response_model=AlertRuleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a threshold alert rule",
)
def create_alert_rule(
    payload: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    return create_rule(db, payload)


@router.get(
    "/alert-rules",
    response_model=list[AlertRuleRead],
    summary="List active alert rules",
)
def get_alert_rules(
    patient_id: uuid.UUID | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    return list_rules(db, patient_id=patient_id)
