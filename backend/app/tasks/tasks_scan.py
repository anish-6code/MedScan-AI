"""
app/tasks/tasks_scan.py

Celery task: process_scan
  1. Mark scan status = processing
  2. Run the full DICOM preprocessing pipeline
  3. Mark scan status = preprocessed
  On any error: mark status = failed and retry (up to 3×)
"""
import logging

from celery import Task

from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.process_scan",
    max_retries=3,
    default_retry_delay=5,      # seconds between retries
    acks_late=True,
)
def process_scan(self: Task, scan_id: str) -> dict:
    """
    Main async DICOM processing task.

    Called automatically right after upload (via .delay()) and can also
    be called directly for standalone testing:

        from app.tasks.tasks_scan import process_scan
        result = process_scan(scan_id='<uuid>')
        print(result['shape'], result['modality'])
    """
    # Import here to avoid circular imports at module load time
    from app.db.session import SessionLocal
    from app.crud.scan import get_scan_by_id, update_scan_status
    from app.services.dicom_processor import preprocess
    import uuid

    db = SessionLocal()
    try:
        # ── 1. Fetch scan record ───────────────────────────────────────────────
        scan = get_scan_by_id(db, uuid.UUID(scan_id))
        if not scan:
            logger.error("process_scan: scan %s not found — skipping", scan_id)
            return {"scan_id": scan_id, "error": "scan not found"}

        # ── 2. Set status → processing ─────────────────────────────────────────
        update_scan_status(db, scan.id, "processing")
        logger.info("process_scan: scan %s → processing", scan_id)

        # ── 3. Run preprocessing pipeline ─────────────────────────────────────
        result = preprocess(file_path=scan.file_path, scan_id=scan_id)
        logger.info(
            "process_scan: scan %s preprocessed — modality=%s shape=%s",
            scan_id, result["modality"], result["shape"],
        )

        # ── 4. Set status → preprocessed ──────────────────────────────────────
        update_scan_status(db, scan.id, "preprocessed")

        # ── 5. Chain → AI inference task ──────────────────────────────────────
        from app.tasks.tasks_ai import run_ai_inference
        run_ai_inference.delay(scan_id)
        logger.info("process_scan: chained run_ai_inference for scan %s", scan_id)

        return {
            "scan_id":     scan_id,
            "modality":    result["modality"],
            "shape":       result["shape"],
            "output_path": result["output_path"],
        }

    except Exception as exc:
        logger.exception("process_scan: scan %s failed — %s", scan_id, exc)
        # Mark as failed in DB before retrying
        try:
            update_scan_status(db, uuid.UUID(scan_id), "failed")
        except Exception:
            pass
        # Celery retry — exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 5)

    finally:
        db.close()
