"""
app/routers/reports.py

GET /scans/{scan_id}/report.pdf
  — Generates (or returns cached) a doctor-facing PDF report for the scan.
"""
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.crud.patient import get_patient_by_id
from app.crud.scan import get_scan_by_id
from app.crud.scan_result import get_result_by_scan_id
from app.dependencies import get_current_doctor, get_db
from app.models.user import User
from app.services.report_generator import generate_report

router = APIRouter(prefix="/scans", tags=["reports"])


@router.get(
    "/{scan_id}/report.pdf",
    response_class=FileResponse,
    summary="Download AI scan report as PDF",
)
def download_report(
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    """
    Generates (first call) or returns cached PDF report for a scan.
    Requires scan status = done (AI results must exist).
    """
    scan = get_scan_by_id(db, scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Scan {scan_id} not found.")

    result = get_result_by_scan_id(db, scan_id)

    # ── Return cached PDF if it exists ─────────────────────────────────────────
    cached_path = os.path.join(settings.REPORTS_DIR, f"{scan_id}.pdf")
    if result and result.report_path and os.path.exists(result.report_path):
        return FileResponse(
            result.report_path,
            media_type="application/pdf",
            filename=f"medscan_report_{str(scan_id)[:8]}.pdf",
        )
    if os.path.exists(cached_path):
        return FileResponse(
            cached_path,
            media_type="application/pdf",
            filename=f"medscan_report_{str(scan_id)[:8]}.pdf",
        )

    # ── Generate PDF on demand ─────────────────────────────────────────────────
    patient = get_patient_by_id(db, scan.patient_id)
    patient_dict = {
        "id":               str(scan.patient_id),
        "name":             getattr(patient, "name", "—") if patient else "—",
        "date_of_birth":    str(getattr(patient, "date_of_birth", "—")) if patient else "—",
        "assigned_doctor":  str(getattr(patient, "assigned_doctor_id", "—")) if patient else "—",
    }
    scan_dict = {
        "original_filename": scan.original_filename,
        "modality":          "—",
        "upload_time":       scan.upload_time.strftime("%Y-%m-%d %H:%M UTC"),
        "status":            scan.status,
    }
    result_dict = None
    overlay_path = None
    if result:
        result_dict  = {
            "confidence_score": result.confidence_score,
            "findings_json":    result.findings_json or {},
        }
        overlay_path = result.overlay_path

    pdf_path = generate_report(
        scan_id=str(scan_id),
        patient=patient_dict,
        scan=scan_dict,
        result=result_dict,
        overlay_path=overlay_path,
    )

    # ── Persist report_path on result row ──────────────────────────────────────
    if result:
        result.report_path = pdf_path
        db.commit()

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"medscan_report_{str(scan_id)[:8]}.pdf",
    )
