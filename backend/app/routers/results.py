import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.scan_result import get_result_by_scan_id
from app.dependencies import get_current_doctor, get_db
from app.models.user import User
from app.schemas.scan_result import ScanResultRead

router = APIRouter(prefix="/results", tags=["results"])


@router.get(
    "/{scan_id}",
    response_model=ScanResultRead,
    summary="Get AI inference results for a scan",
)
def get_result(
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    """
    Returns the AI segmentation result for a given scan.
    Available once scan status = 'done'.
    """
    result = get_result_by_scan_id(db, scan_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No AI result found for scan {scan_id}. "
                   "Processing may still be in progress.",
        )
    return result
