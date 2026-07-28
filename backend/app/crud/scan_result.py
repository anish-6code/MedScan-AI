import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.scan_result import ScanResult


def create_scan_result(
    db: Session,
    *,
    scan_id: uuid.UUID,
    mask_path: str | None = None,
    overlay_path: str | None = None,
    confidence_score: float | None = None,
    findings_json: dict[str, Any] | None = None,
) -> ScanResult:
    result = ScanResult(
        scan_id=scan_id,
        mask_path=mask_path,
        overlay_path=overlay_path,
        confidence_score=confidence_score,
        findings_json=findings_json,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_result_by_scan_id(db: Session, scan_id: uuid.UUID) -> ScanResult | None:
    return db.query(ScanResult).filter(ScanResult.scan_id == scan_id).first()
