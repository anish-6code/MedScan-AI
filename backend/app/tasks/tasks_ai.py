"""
app/tasks/tasks_ai.py

Celery task: run_ai_inference
  Automatically triggered after process_scan succeeds.
  1. Load preprocessed .npy from disk
  2. Run U-Net inference → mask + bboxes + confidence
  3. Save mask .npy + overlay .png
  4. Insert ScanResult row
  5. Update scans.status = done
"""
import logging
import os
import uuid

import numpy as np

from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.run_ai_inference",
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
)
def run_ai_inference(self, scan_id: str) -> dict:
    """
    Run U-Net segmentation on a preprocessed scan and store results.

    Can also be called directly for standalone testing:
        from app.tasks.tasks_ai import run_ai_inference
        result = run_ai_inference('<scan_id>')
        print(result['confidence'], result['findings'])
    """
    from app.config import settings
    from app.crud.scan import get_scan_by_id, update_scan_status
    from app.crud.scan_result import create_scan_result, get_result_by_scan_id
    from app.db.session import SessionLocal
    from app.services.ai_inference import run_inference, save_mask, save_overlay

    db = SessionLocal()
    try:
        scan_uuid = uuid.UUID(scan_id)

        # ── 1. Fetch scan ──────────────────────────────────────────────────────
        scan = get_scan_by_id(db, scan_uuid)
        if not scan:
            logger.error("run_ai_inference: scan %s not found", scan_id)
            return {"scan_id": scan_id, "error": "scan not found"}

        # ── 2. Load preprocessed .npy ─────────────────────────────────────────
        npy_path = os.path.join(settings.PREPROCESSED_DIR, f"{scan_id}.npy")
        if not os.path.exists(npy_path):
            raise FileNotFoundError(f"Preprocessed file not found: {npy_path}")

        array = np.load(npy_path).astype("float32")
        logger.info("run_ai_inference: loaded array %s shape=%s", scan_id, array.shape)

        # ── 3. Run inference ───────────────────────────────────────────────────
        result = run_inference(array)
        logger.info(
            "run_ai_inference: scan %s confidence=%.3f regions=%d",
            scan_id,
            result["confidence"],
            result["findings_json"]["num_regions"],
        )

        # ── 4. Save outputs ────────────────────────────────────────────────────
        mask_path    = save_mask(result["mask"], scan_id)
        overlay_path = save_overlay(array, result["mask"], scan_id)

        # ── 5. Persist result row (upsert-safe — unique constraint on scan_id) ─
        existing = get_result_by_scan_id(db, scan_uuid)
        if not existing:
            create_scan_result(
                db,
                scan_id=scan_uuid,
                mask_path=mask_path,
                overlay_path=overlay_path,
                confidence_score=result["confidence"],
                findings_json=result["findings_json"],
            )

        # ── 6. Mark scan done ──────────────────────────────────────────────────
        update_scan_status(db, scan_uuid, "done")
        logger.info("run_ai_inference: scan %s → done", scan_id)

        return {
            "scan_id":     scan_id,
            "confidence":  result["confidence"],
            "findings":    result["findings_json"],
            "mask_path":   mask_path,
            "overlay_path": overlay_path,
        }

    except Exception as exc:
        logger.exception("run_ai_inference: scan %s failed — %s", scan_id, exc)
        try:
            update_scan_status(db, uuid.UUID(scan_id), "failed")
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 10)

    finally:
        db.close()
