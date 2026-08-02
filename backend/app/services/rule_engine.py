"""
app/services/rule_engine.py

Evaluates a VitalsReading against all applicable AlertRules and creates
Alert records for any breached thresholds.

Algorithm:
  1. Load global rules + patient-specific overrides for the reading's patient.
  2. For each rule, check if the measured vital is outside [min_value, max_value].
  3. If breached, count how many of the N most recent readings also breach this rule.
  4. Only create an alert if consecutive_breaches_required readings all breach
     (prevents false positives from a single noisy sample).
  5. Skip if an active alert already exists for this rule (dedup).
  6. Broadcast the alert via WebSocket to all connected doctors (Module 10).
"""
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertRule, AlertStatus, AlertSeverity, VitalSignEnum
from app.models.vitals import VitalsReading


# ── Default global thresholds (loaded by seed if alert_rules is empty) ────────
DEFAULT_RULES: list[dict] = [
    {"vital_sign": "heart_rate",        "min_value":  40, "max_value": 130, "severity": "moderate", "consecutive_breaches_required": 2},
    {"vital_sign": "heart_rate",        "min_value":  20, "max_value": 160, "severity": "critical",  "consecutive_breaches_required": 1},
    {"vital_sign": "spo2",              "min_value":  90, "max_value": None, "severity": "moderate", "consecutive_breaches_required": 2},
    {"vital_sign": "spo2",              "min_value":  85, "max_value": None, "severity": "critical",  "consecutive_breaches_required": 1},
    {"vital_sign": "systolic_bp",       "min_value":  80, "max_value": 180, "severity": "moderate", "consecutive_breaches_required": 2},
    {"vital_sign": "systolic_bp",       "min_value":  60, "max_value": 200, "severity": "critical",  "consecutive_breaches_required": 1},
    {"vital_sign": "temperature",       "min_value":  35, "max_value":  38, "severity": "moderate", "consecutive_breaches_required": 2},
    {"vital_sign": "temperature",       "min_value":  33, "max_value":  40, "severity": "critical",  "consecutive_breaches_required": 1},
    {"vital_sign": "respiratory_rate",  "min_value":   8, "max_value":  25, "severity": "moderate", "consecutive_breaches_required": 2},
    {"vital_sign": "respiratory_rate",  "min_value":   5, "max_value":  35, "severity": "critical",  "consecutive_breaches_required": 1},
]


def _get_vital_value(reading: VitalsReading, vital: str) -> float | None:
    return getattr(reading, vital, None)


def _is_breached(value: float, rule: AlertRule) -> bool:
    if rule.min_value is not None and value < rule.min_value:
        return True
    if rule.max_value is not None and value > rule.max_value:
        return True
    return False


def _count_consecutive_breaches(
    db: Session, patient_id: uuid.UUID, rule: AlertRule, current_value: float, n: int
) -> int:
    """Count the last N readings that also breach this rule (including current)."""
    recent = (
        db.query(VitalsReading)
        .filter(VitalsReading.patient_id == patient_id)
        .order_by(VitalsReading.recorded_at.desc())
        .limit(n)
        .all()
    )
    count = 0
    for r in recent:
        v = _get_vital_value(r, rule.vital_sign.value)
        if v is not None and _is_breached(v, rule):
            count += 1
        else:
            break  # must be consecutive
    return count


def _active_alert_exists(db: Session, patient_id: uuid.UUID, rule_id: uuid.UUID) -> bool:
    return db.query(Alert).filter(
        Alert.patient_id == patient_id,
        Alert.rule_id    == rule_id,
        Alert.status     == AlertStatus.active,
    ).count() > 0


def _build_message(vital: str, value: float, rule: AlertRule) -> str:
    parts = []
    if rule.min_value is not None and value < rule.min_value:
        parts.append(f"{vital.replace('_', ' ')} {value} < min {rule.min_value}")
    if rule.max_value is not None and value > rule.max_value:
        parts.append(f"{vital.replace('_', ' ')} {value} > max {rule.max_value}")
    return "; ".join(parts)


def run_rule_engine(db: Session, reading_id: uuid.UUID) -> list[Alert]:
    """
    Main entry point. Returns list of newly created Alert objects.
    Called by Celery task after each vitals ingest.
    """
    reading = db.query(VitalsReading).filter(VitalsReading.id == reading_id).first()
    if not reading:
        return []

    # Load rules: patient-specific first, then global (patient_id IS NULL)
    rules = (
        db.query(AlertRule)
        .filter(
            AlertRule.is_active == True,
            (AlertRule.patient_id == reading.patient_id) | (AlertRule.patient_id == None),
        )
        .all()
    )

    # Seed defaults if no rules exist at all
    if not rules:
        _seed_defaults(db)
        rules = db.query(AlertRule).filter(AlertRule.is_active == True, AlertRule.patient_id == None).all()

    created_alerts: list[Alert] = []

    for rule in rules:
        value = _get_vital_value(reading, rule.vital_sign.value)
        if value is None:
            continue
        if not _is_breached(value, rule):
            continue
        if _active_alert_exists(db, reading.patient_id, rule.id):
            continue

        # Check consecutive breach count
        breaches = _count_consecutive_breaches(
            db, reading.patient_id, rule, value, rule.consecutive_breaches_required
        )
        if breaches < rule.consecutive_breaches_required:
            continue

        alert = Alert(
            patient_id  = reading.patient_id,
            rule_id     = rule.id,
            reading_id  = reading.id,
            vital_sign  = rule.vital_sign,
            value       = value,
            severity    = rule.severity,
            status      = AlertStatus.active,
            message     = _build_message(rule.vital_sign.value, value, rule),
        )
        db.add(alert)
        created_alerts.append(alert)

    if created_alerts:
        db.commit()
        for a in created_alerts:
            db.refresh(a)

        # Broadcast via WebSocket (Module 10)
        try:
            from app.services.ws_manager import manager
            import asyncio
            payload = {
                "type":      "alert",
                "patient_id": str(reading.patient_id),
                "alerts": [
                    {
                        "id":         str(a.id),
                        "vital_sign": a.vital_sign.value,
                        "value":      a.value,
                        "severity":   a.severity.value,
                        "message":    a.message,
                    }
                    for a in created_alerts
                ],
            }
            asyncio.create_task(manager.broadcast(payload))
        except Exception:
            pass

    return created_alerts


def _seed_defaults(db: Session) -> None:
    """Insert global default rules on first use."""
    for rule_data in DEFAULT_RULES:
        rule = AlertRule(
            patient_id = None,
            vital_sign = VitalSignEnum(rule_data["vital_sign"]),
            min_value  = rule_data.get("min_value"),
            max_value  = rule_data.get("max_value"),
            severity   = AlertSeverity(rule_data["severity"]),
            consecutive_breaches_required = rule_data.get("consecutive_breaches_required", 1),
            is_active  = True,
        )
        db.add(rule)
    db.commit()
