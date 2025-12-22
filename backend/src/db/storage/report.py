"""
Report Storage - Persistence layer for generated reports.

Provides database operations for saving, retrieving, and sharing reports.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from src.config.settings import REPORTS_DIR
from src.db.storage.base import BaseStorage
from src.db.models import ReportModel, ReportStatus

logger = logging.getLogger(__name__)


class ReportStorage(BaseStorage):
    """Storage layer for report management with share link support."""

    MAX_RECORDS = 100  # Keep last 100 reports per user

    def __init__(self, database_url: Optional[str] = None):
        """Initialize report storage.

        Args:
            database_url: SQLAlchemy database URL (defaults to DATABASE_URL from settings)
        """
        super().__init__(database_url)
        logger.info(f"ReportStorage initialized with database: {self.database_url}")

    def create_report(
        self,
        report_id: str,
        report_type: str,
        title: str,
        source_ids: List[str],
        source_type: str,
        user_id: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Create a new report record in pending state.

        Args:
            report_id: Unique identifier (UUID)
            report_type: Type of report (backtest, portfolio, walkforward, comparison)
            title: Report title
            source_ids: List of source record IDs
            source_type: Type of source records (backtest, portfolio, walkforward)
            user_id: Optional user identifier
            description: Optional description
            config: Optional configuration dict
            db: Optional database session

        Returns:
            Created report as dict
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            record = ReportModel(
                report_id=report_id,
                report_type=report_type,
                title=title,
                description=description,
                source_ids=source_ids,
                source_type=source_type,
                status=ReportStatus.PENDING.value,
                progress=0,
                user_id=user_id,
                config=config,
                created_at=datetime.utcnow(),
            )

            db.add(record)
            db.commit()
            db.refresh(record)

            logger.info(f"Created report {report_id}")
            return self._record_to_dict(record)

        except Exception as e:
            logger.error(f"Failed to create report {report_id}: {e}")
            db.rollback()
            raise
        finally:
            if close_db:
                db.close()

    def get_report(
        self,
        report_id: str,
        user_id: Optional[str] = None,
        include_html: bool = False,
        db: Optional[Session] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get single report by ID.

        Args:
            report_id: Report UUID
            user_id: Optional user ID for filtering
            include_html: Whether to include full HTML content
            db: Optional database session

        Returns:
            Report dict or None if not found
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            query = db.query(ReportModel).filter(
                ReportModel.report_id == report_id
            )

            if user_id:
                query = query.filter(ReportModel.user_id == user_id)

            record = query.first()

            if not record:
                return None

            return self._record_to_dict(record, include_html=include_html)

        finally:
            if close_db:
                db.close()

    def get_report_by_share_token(
        self,
        share_token: str,
        db: Optional[Session] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get report by share token (for public access).

        Args:
            share_token: Share token string
            db: Optional database session

        Returns:
            Report dict with HTML content, or None if not found/expired
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            record = db.query(ReportModel).filter(
                ReportModel.share_token == share_token
            ).first()

            if not record:
                return None

            # Check expiry
            if record.share_expires_at and record.share_expires_at < datetime.utcnow():
                return None

            return self._record_to_dict(record, include_html=True)

        finally:
            if close_db:
                db.close()

    def list_reports(
        self,
        report_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        List reports with filtering and pagination.

        Args:
            report_type: Filter by report type
            status: Filter by status
            start_date: Filter by created_at >= date
            end_date: Filter by created_at <= date
            sort_by: Field to sort by
            sort_order: "asc" or "desc"
            limit: Max records to return
            offset: Pagination offset
            user_id: Filter by user ID
            db: Optional database session

        Returns:
            Dict with 'reports' list and 'total' count
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            query = db.query(ReportModel)

            # Apply filters
            if user_id:
                query = query.filter(ReportModel.user_id == user_id)
            if report_type:
                query = query.filter(ReportModel.report_type == report_type)
            if status:
                query = query.filter(ReportModel.status == status)
            if start_date:
                query = query.filter(ReportModel.created_at >= start_date)
            if end_date:
                from datetime import timedelta
                end_dt = datetime.fromisoformat(end_date) + timedelta(days=1)
                query = query.filter(ReportModel.created_at < end_dt)

            # Get total count before pagination
            total = query.count()

            # Apply sorting
            sort_field = getattr(ReportModel, sort_by, ReportModel.created_at)
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_field))
            else:
                query = query.order_by(desc(sort_field))

            # Apply pagination
            query = query.offset(offset).limit(limit)

            records = query.all()
            reports = [self._record_to_dict(record) for record in records]

            return {"reports": reports, "total": total}

        finally:
            if close_db:
                db.close()

    def update_status(
        self,
        report_id: str,
        status: str,
        progress: Optional[int] = None,
        error_message: Optional[str] = None,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Update report status and progress.

        Args:
            report_id: Report UUID
            status: New status value
            progress: Optional progress percentage (0-100)
            error_message: Optional error message for failed status
            user_id: Optional user ID filter
            db: Optional database session

        Returns:
            True if updated, False if not found
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            query = db.query(ReportModel).filter(
                ReportModel.report_id == report_id
            )

            if user_id:
                query = query.filter(ReportModel.user_id == user_id)

            record = query.first()

            if not record:
                return False

            record.status = status
            if progress is not None:
                record.progress = progress
            if error_message is not None:
                record.error_message = error_message
            if status == ReportStatus.COMPLETED.value:
                record.completed_at = datetime.utcnow()

            db.commit()
            logger.debug(f"Updated report {report_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to update report status {report_id}: {e}")
            db.rollback()
            return False
        finally:
            if close_db:
                db.close()

    def save_content(
        self,
        report_id: str,
        html_content: str,
        html_filename: Optional[str] = None,
        metrics_summary: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Save generated report content.

        Args:
            report_id: Report UUID
            html_content: Generated HTML content
            html_filename: Optional filename for download
            metrics_summary: Optional summary metrics for list display
            user_id: Optional user ID filter
            db: Optional database session

        Returns:
            True if saved, False if not found
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            query = db.query(ReportModel).filter(
                ReportModel.report_id == report_id
            )

            if user_id:
                query = query.filter(ReportModel.user_id == user_id)

            record = query.first()

            if not record:
                return False

            record.html_content = html_content
            if html_filename:
                record.html_filename = html_filename
            if metrics_summary:
                record.metrics_summary = metrics_summary
            record.status = ReportStatus.COMPLETED.value
            record.progress = 100
            record.completed_at = datetime.utcnow()

            db.commit()
            logger.info(f"Saved content for report {report_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save report content {report_id}: {e}")
            db.rollback()
            return False
        finally:
            if close_db:
                db.close()

    def set_share_token(
        self,
        report_id: str,
        share_token: str,
        expires_at: datetime,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Set share token for a report.

        Args:
            report_id: Report UUID
            share_token: Generated share token
            expires_at: Token expiration datetime
            user_id: Optional user ID filter
            db: Optional database session

        Returns:
            True if set, False if not found
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            query = db.query(ReportModel).filter(
                ReportModel.report_id == report_id
            )

            if user_id:
                query = query.filter(ReportModel.user_id == user_id)

            record = query.first()

            if not record:
                return False

            record.share_token = share_token
            record.share_expires_at = expires_at

            db.commit()
            logger.info(f"Set share token for report {report_id}, expires at {expires_at}")
            return True

        except Exception as e:
            logger.error(f"Failed to set share token for {report_id}: {e}")
            db.rollback()
            return False
        finally:
            if close_db:
                db.close()

    def clear_share_token(
        self,
        report_id: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Clear/revoke share token for a report.

        Args:
            report_id: Report UUID
            user_id: Optional user ID filter
            db: Optional database session

        Returns:
            True if cleared, False if not found
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            query = db.query(ReportModel).filter(
                ReportModel.report_id == report_id
            )

            if user_id:
                query = query.filter(ReportModel.user_id == user_id)

            record = query.first()

            if not record:
                return False

            record.share_token = None
            record.share_expires_at = None

            db.commit()
            logger.info(f"Cleared share token for report {report_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to clear share token for {report_id}: {e}")
            db.rollback()
            return False
        finally:
            if close_db:
                db.close()

    def delete_report(
        self,
        report_id: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Delete report and its associated files.

        Args:
            report_id: Report UUID
            user_id: Optional user ID filter
            db: Optional database session

        Returns:
            True if deleted, False if not found
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            query = db.query(ReportModel).filter(
                ReportModel.report_id == report_id
            )

            if user_id:
                query = query.filter(ReportModel.user_id == user_id)

            record = query.first()

            if not record:
                return False

            # Delete HTML file if exists
            if record.html_filename:
                html_path = REPORTS_DIR / record.html_filename
                if html_path.exists():
                    try:
                        os.remove(html_path)
                        logger.debug(f"Deleted report file: {html_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete report file {html_path}: {e}")

            db.delete(record)
            db.commit()

            logger.info(f"Deleted report {report_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete report {report_id}: {e}")
            db.rollback()
            return False
        finally:
            if close_db:
                db.close()

    def _record_to_dict(
        self,
        record: ReportModel,
        include_html: bool = False,
    ) -> Dict[str, Any]:
        """Convert database record to dictionary."""
        result = {
            "report_id": record.report_id,
            "report_type": record.report_type,
            "title": record.title,
            "description": record.description,
            "source_ids": record.source_ids,
            "source_type": record.source_type,
            "status": record.status,
            "progress": record.progress,
            "error_message": record.error_message,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
            "config": record.config,
            "html_filename": record.html_filename,
            "has_share_link": record.share_token is not None,
            "share_expires_at": record.share_expires_at.isoformat() if record.share_expires_at else None,
            "metrics_summary": record.metrics_summary,
        }

        if include_html:
            result["html_content"] = record.html_content

        return result


# Singleton instance
_report_storage: Optional[ReportStorage] = None


def get_report_storage() -> ReportStorage:
    """Get singleton ReportStorage instance."""
    global _report_storage
    if _report_storage is None:
        _report_storage = ReportStorage()
    return _report_storage


__all__ = [
    "ReportStorage",
    "get_report_storage",
]
