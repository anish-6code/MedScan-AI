import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertRule, AlertRuleCreate, AlertStatus


def create_rule(db: Session, payload: "AlertRuleCreate") -> AlertRule:
    from app.models.alert import AlertSeverity, VitalSignEnum
    rule = AlertRule(
        patient_id = payload.patient_id,
        vital_sign = VitalSignEnum(payload.vital_sign),
        min_value  = payload.min_value,
        max_value  = payload.max_value,
        severity   = AlertSeverity(payload.severity),
        consecutive_breaches_required = payload.consecutive_breaches_required,
    )
    db.add(rule); db.commit(); db.refresh(rule)
    return rule


def list_rules(db: Session, patient_id: uuid.UUID | None = None) -> list[AlertRule]:
    q = db.query(AlertRule).filter(AlertRule.is_active == True)
    if patient_id:
        q = q.filter(
            (AlertRule.patient_id == patient_id) | (AlertRule.patient_id == None)
        )
    return q.all()


def list_alerts(
    db: Session,
    patient_id: uuid.UUID | None = None,
    status: str | None = None,
    page: int = 1,
    size: int = 50,
) -> tuple[int, list[Alert]]:
    q = db.query(Alert)
    if patient_id:
        q = q.filter(Alert.patient_id == patient_id)
    if status:
        q = q.filter(Alert.status == status)
    total = q.count()
    items = q.order_by(Alert.triggered_at.desc()).offset((page - 1) * size).limit(size).all()
    return total, items


def acknowledge_alert(
    db: Session, alert_id: uuid.UUID, doctor_id: uuid.UUID
) -> Alert | None:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return None
    alert.status           = AlertStatus.acknowledged
    alert.acknowledged_at  = datetime.now(timezone.utc)
    alert.acknowledged_by  = doctor_id
    db.commit(); db.refresh(alert)
    return alert
