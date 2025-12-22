"""
Report Model - SQLAlchemy model for report generation and sharing.

This module defines the database table for storing:
- Generated report metadata and content
- Report generation status and progress
- Share link tokens with expiry
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Integer, String, Text

from src.db.models.base import Base, SafeJSON


class ReportStatus(str, Enum):
    """Report generation status values."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportType(str, Enum):
    """Supported report types."""
    BACKTEST = "backtest"
    PORTFOLIO = "portfolio"
    WALKFORWARD = "walkforward"
    COMPARISON = "comparison"


class ReportModel(Base):
    """
    Report Model - Stores generated reports for viewing, download, and sharing.

    Supports unified reports for:
    - Single backtest results
    - Portfolio backtest results
    - Walk-forward optimization results
    - Comparison reports (multiple results combined)
    """
    __tablename__ = "reports"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique identifier for the report
    report_id = Column(String(36), unique=True, nullable=False, index=True)

    # Report metadata
    report_type = Column(String(50), nullable=False, index=True)  # backtest, portfolio, walkforward, comparison
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Source references (JSON array of IDs)
    # e.g., ["backtest_123", "backtest_456"] for comparison reports
    source_ids = Column(SafeJSON, nullable=False)
    source_type = Column(String(50), nullable=False)  # backtest, portfolio, walkforward

    # Status and progress
    status = Column(String(20), default=ReportStatus.PENDING.value, nullable=False, index=True)
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # User identification
    user_id = Column(String(255), nullable=True, index=True)

    # Report configuration (JSON)
    # e.g., {"sections": ["overview", "charts"], "chart_format": "interactive"}
    config = Column(SafeJSON, nullable=True)

    # Generated HTML content (cached for fast re-viewing)
    html_content = Column(Text, nullable=True)

    # File references (for downloadable files)
    html_filename = Column(String(255), nullable=True)

    # Share link support
    share_token = Column(String(64), nullable=True, unique=True, index=True)
    share_expires_at = Column(DateTime, nullable=True)

    # Summary metrics for list display (JSON format)
    # e.g., {"total_return": 25.5, "sharpe_ratio": 1.8, "num_sources": 2}
    metrics_summary = Column(SafeJSON, nullable=True)

    def __repr__(self):
        return (
            f"<Report(id={self.report_id}, "
            f"type={self.report_type}, "
            f"status={self.status}, "
            f"title={self.title[:30] + '...' if self.title and len(self.title) > 30 else self.title})>"
        )


__all__ = [
    "ReportModel",
    "ReportStatus",
    "ReportType",
]
