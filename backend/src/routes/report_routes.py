"""
Report Center API routes.

Handles:
- Report generation (background task)
- Report list/detail/download
- Share link generation and public access
"""
import uuid
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

from src.config.settings import REPORTS_DIR
from src.db.storage.report import get_report_storage
from src.db.models.report import ReportStatus, ReportType
from src.service.report_generator import get_report_generator
from src.utils.auth import get_current_user
from src.utils.share_token import generate_share_token, verify_share_token

logger = logging.getLogger(__name__)

# Error message constants
MSG_REPORT_NOT_FOUND = "Report not found"
router = APIRouter(prefix="/reports", tags=["reports"])


# ========== Pydantic Models ==========


class ReportGenerateRequest(BaseModel):
    """Request model for report generation."""
    report_type: str = Field(
        ...,
        description="Type of report: backtest, portfolio, walkforward, comparison",
    )
    source_ids: list[str] = Field(
        ...,
        description="List of source record IDs to include",
    )
    title: Optional[str] = Field(
        None,
        description="Custom title for the report",
    )
    description: Optional[str] = Field(
        None,
        description="Custom description for the report",
    )
    config: Optional[dict] = Field(
        None,
        description="Report configuration (sections, chart_format, etc.)",
    )


class ReportListQuery(BaseModel):
    """Query model for report list."""
    report_type: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    limit: int = 50
    offset: int = 0


class ShareLinkRequest(BaseModel):
    """Request model for share link generation."""
    expires_in_hours: int = Field(
        default=168,  # 7 days
        ge=1,
        le=720,  # 30 days max
        description="Expiration time in hours",
    )


# ========== Background Task Handler ==========


async def _run_report_generation(
    report_id: str,
    report_type: str,
    source_ids: list[str],
    config: dict,
    user_id: Optional[str],
):
    """Background task for report generation."""
    try:
        generator = get_report_generator()
        await generator.generate_report(
            report_id=report_id,
            report_type=report_type,
            source_ids=source_ids,
            config=config,
            user_id=user_id,
        )
    except Exception as e:
        logger.error(f"Report generation failed for {report_id}: {e}", exc_info=True)
        # Error status is set in generator


# ========== Report CRUD Endpoints ==========


@router.get("")
def list_reports(
    report_type: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user),
) -> dict:
    """
    List generated reports with filtering and pagination.
    """
    storage = get_report_storage()
    user_id = user.get("sub") if user else None

    return storage.list_reports(
        report_type=report_type,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
        user_id=user_id,
    )


@router.post("")
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Generate a new report as a background task.
    
    Returns the report ID immediately; poll status via GET /reports/{id}.
    """
    storage = get_report_storage()
    user_id = user.get("sub") if user else None

    # Validate report type
    try:
        ReportType(request.report_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report_type. Must be one of: {[t.value for t in ReportType]}",
        )

    # Validate source_ids not empty
    if not request.source_ids:
        raise HTTPException(status_code=400, detail="source_ids cannot be empty")

    # Create report record
    report_id = str(uuid.uuid4())
    title = request.title or f"{request.report_type.title()} Report"

    # Determine source_type from report_type
    source_type = request.report_type
    if request.report_type == "comparison":
        source_type = "backtest"  # Comparison typically compares backtests

    storage.create_report(
        report_id=report_id,
        report_type=request.report_type,
        title=title,
        description=request.description,
        source_ids=request.source_ids,
        source_type=source_type,
        config=request.config,
        user_id=user_id,
    )

    # Add background task for generation
    background_tasks.add_task(
        _run_report_generation,
        report_id=report_id,
        report_type=request.report_type,
        source_ids=request.source_ids,
        config=request.config or {},
        user_id=user_id,
    )

    logger.info(f"Report generation started: {report_id}")

    return {
        "report_id": report_id,
        "status": ReportStatus.PENDING.value,
        "message": "Report generation started",
    }


@router.get("/{report_id}")
def get_report(
    report_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Get report details including HTML content if completed.
    """
    storage = get_report_storage()
    user_id = user.get("sub") if user else None

    report = storage.get_report(report_id, user_id=user_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return report


@router.delete("/{report_id}")
def delete_report(
    report_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Delete a report and its generated files.
    """
    storage = get_report_storage()
    user_id = user.get("sub") if user else None

    deleted = storage.delete_report(report_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")

    return {"status": "ok", "message": "Report deleted"}


# ========== Download Endpoint ==========


@router.get("/{report_id}/download")
def download_report(
    report_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Download the generated HTML report file.
    """
    storage = get_report_storage()
    user_id = user.get("sub") if user else None

    report = storage.get_report(report_id, user_id=user_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.get("status") != ReportStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Report not ready. Current status: {report.get('status')}",
        )

    html_filename = report.get("html_filename")
    if not html_filename:
        raise HTTPException(status_code=404, detail="Report file not found")

    file_path = REPORTS_DIR / html_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found on disk")

    # Use title for download filename
    download_name = f"{report.get('title', 'report').replace(' ', '_')}.html"

    return FileResponse(
        path=str(file_path),
        filename=download_name,
        media_type="text/html",
    )


# ========== Share Link Endpoints ==========


@router.post("/{report_id}/share")
def create_share_link(
    report_id: str,
    request: ShareLinkRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Generate a share link for a completed report.
    
    Returns a signed URL that expires after the specified duration.
    """
    storage = get_report_storage()
    user_id = user.get("sub") if user else None

    report = storage.get_report(report_id, user_id=user_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.get("status") != ReportStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail="Only completed reports can be shared",
        )

    # Calculate expiry
    expires_at = datetime.utcnow() + timedelta(hours=request.expires_in_hours)

    # Generate token
    share_token = generate_share_token(report_id, expires_at)

    # Save token to database
    storage.set_share_token(
        report_id=report_id,
        share_token=share_token,
        expires_at=expires_at,
        user_id=user_id,
    )

    return {
        "share_token": share_token,
        "share_url": f"/report/shared/{share_token}",
        "expires_at": expires_at.isoformat(),
        "expires_in_hours": request.expires_in_hours,
    }


@router.delete("/{report_id}/share")
def revoke_share_link(
    report_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Revoke an existing share link for a report.
    """
    storage = get_report_storage()
    user_id = user.get("sub") if user else None

    report = storage.get_report(report_id, user_id=user_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    storage.clear_share_token(report_id, user_id=user_id)

    return {"status": "ok", "message": "Share link revoked"}


# ========== Public Shared Report Endpoint ==========


@router.get("/shared/{share_token}", dependencies=[])
def get_shared_report(share_token: str) -> HTMLResponse:
    """
    Access a shared report using its share token.
    
    This endpoint is public (no authentication required).
    """
    # Verify token
    token_data = verify_share_token(share_token)
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired share link",
        )

    # Get report (no user_id check for shared reports)
    storage = get_report_storage()
    report = storage.get_report_by_share_token(share_token)

    if not report:
        raise HTTPException(status_code=404, detail="Shared report not found")

    if report.get("status") != ReportStatus.COMPLETED.value:
        raise HTTPException(status_code=404, detail="Report not available")

    # Return HTML content
    html_content = report.get("html_content")
    if not html_content:
        # Try to read from file
        html_filename = report.get("html_filename")
        if html_filename:
            file_path = REPORTS_DIR / html_filename
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    html_content = f.read()

    if not html_content:
        raise HTTPException(status_code=404, detail="Report content not found")

    return HTMLResponse(content=html_content)
