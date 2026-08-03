"""
app/tasks/tasks_vitals.py

Celery task: triggered after each vitals ingest.
Runs the rule engine to check thresholds and create alerts.
"""
from app.worker import celery_app
from app.db.session import SessionLocal


@celery_app.task(
    name="tasks.check_vitals_rules",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
)
def check_vitals_rules(self, reading_id: str):
    """
    Check a newly ingested VitalsReading against all applicable alert rules.
    Creates Alert records for any consecutive threshold breaches.
    """
    import uuid
    from app.services.rule_engine import run_rule_engine

    db = SessionLocal()
    try:
        alerts = run_rule_engine(db, uuid.UUID(reading_id))
        return {
            "reading_id": reading_id,
            "alerts_created": len(alerts),
            "alert_ids": [str(a.id) for a in alerts],
        }
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()
