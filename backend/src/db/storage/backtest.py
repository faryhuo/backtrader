"""
Backtest Storage - Persistence layer for backtest history.

Provides database operations for saving and retrieving backtest results.
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from src.config.settings import DATABASE_URL, IMAGES_DIR
from src.db.storage.base import BaseStorage
from src.db.models import BacktestHistoryModel, init_database

logger = logging.getLogger(__name__)


class BacktestStorage(BaseStorage):
    """Storage layer for backtest history with auto-cleanup."""

    MAX_RECORDS = 100  # Keep last 100 backtests

    def __init__(self, database_url: Optional[str] = None):
        """Initialize backtest storage.

        Args:
            database_url: SQLAlchemy database URL (defaults to DATABASE_URL from settings)
        """
        super().__init__(database_url)
        logger.info(f"BacktestStorage initialized with database: {self.database_url}")

    def save_backtest(
        self,
        backtest_id: str,
        config: Dict[str, Any],
        metrics: Dict[str, Any],
        plot_filename: Optional[str] = None,
        ai_analysis: Optional[str] = None,
        strategy_code: Optional[str] = None,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> BacktestHistoryModel:
        """
        Save backtest result to database.

        Args:
            backtest_id: Unique identifier (UUID)
            config: Backtest configuration dict
            metrics: Complete metrics dict from backtest engine
            plot_filename: Plot image filename (e.g., "uuid.png")
            ai_analysis: AI analysis text
            strategy_code: Strategy source code snapshot
            user_id: Optional user identifier
            db: Optional database session

        Returns:
            Saved BacktestHistoryModel instance
        """
        with self.managed_session(db) as session:
            try:
                # Extract key metrics for indexing
                final_value = metrics.get("final_value", 0.0)
                total_return = metrics.get("returns", 0.0)

                record = BacktestHistoryModel(
                    backtest_id=backtest_id,
                    user_id=user_id,
                    ticker=config["ticker"],
                    start_date=config["start_date"],
                    end_date=config["end_date"],
                    initial_cash=config.get("initial_cash", 100000.0),
                    commission=config.get("commission", 0.0005),
                    stake=config.get("stake", 100),
                    strategy_name=config.get("strategy_name", "unknown"),
                    created_at=datetime.utcnow(),
                    final_value=final_value,
                    total_return=total_return,
                    sharpe_ratio=metrics.get("sharpe"),
                    max_drawdown=metrics.get("drawdown", 0.0),
                    total_trades=metrics.get("trade_details", {}).get("total_trades", 0),
                    winning_trades=metrics.get("trade_details", {}).get("winning_trades", 0),
                    losing_trades=metrics.get("trade_details", {}).get("losing_trades", 0),
                    metrics=metrics,
                    ai_analysis=ai_analysis,
                    strategy_code=strategy_code,
                    plot_filename=plot_filename,
                    params=config.get("params"),
                )

                session.add(record)
                session.flush()  # Get ID before commit

                logger.info(f"Saved backtest {backtest_id} to database")

                # Auto-cleanup old records
                self._cleanup_old_records(session)

                return record

            except Exception as e:
                logger.error(f"Failed to save backtest {backtest_id}: {e}")
                raise

    def _cleanup_old_records(self, db: Session) -> None:
        """
        Delete old records beyond MAX_RECORDS limit.
        Also deletes associated plot image files.
        """
        try:
            count = db.query(BacktestHistoryModel).count()

            if count > self.MAX_RECORDS:
                # Get records to delete (oldest first)
                to_delete = (
                    db.query(BacktestHistoryModel)
                    .order_by(asc(BacktestHistoryModel.created_at))
                    .limit(count - self.MAX_RECORDS)
                    .all()
                )

                for record in to_delete:
                    # Delete plot file if exists
                    if record.plot_filename:
                        plot_path = IMAGES_DIR / record.plot_filename
                        if plot_path.exists():
                            try:
                                os.remove(plot_path)
                                logger.debug(f"Deleted plot file: {plot_path}")
                            except Exception as e:
                                logger.warning(f"Failed to delete plot {plot_path}: {e}")

                    db.delete(record)

                db.commit()
                logger.info(f"Cleaned up {len(to_delete)} old backtest records")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            db.rollback()

    def _cleanup_corrupted_records(self, db: Session) -> None:
        """
        Delete records with corrupted JSON data.

        This method attempts to find and remove records that have invalid
        JSON in metrics or ai_analysis columns.
        """
        try:
            from sqlalchemy import text

            # Use raw SQL to identify and delete corrupted records
            # This is safer than trying to load them through ORM
            result = db.execute(
                text(
                    "DELETE FROM backtest_history WHERE "
                    "metrics IS NULL OR metrics = '' OR "
                    "ai_analysis = ''"
                )
            )
            deleted_count = result.rowcount
            db.commit()

            if deleted_count > 0:
                logger.warning(f"Deleted {deleted_count} corrupted backtest records")

        except Exception as e:
            logger.error(f"Failed to cleanup corrupted records: {e}")
            db.rollback()

    def list_backtests(
        self,
        ticker: Optional[str] = None,
        strategy_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        List backtest history with filtering and sorting.

        Args:
            ticker: Filter by ticker symbol
            strategy_name: Filter by strategy name
            start_date: Filter by run date >= this date (YYYY-MM-DD)
            end_date: Filter by run date <= this date (YYYY-MM-DD)
            sort_by: Field to sort by (created_at, total_return, sharpe_ratio)
            sort_order: "asc" or "desc"
            limit: Max records to return
            offset: Pagination offset
            user_id: Filter by user ID
            db: Optional database session

        Returns:
            Dict with 'backtests' list and 'total' count
        """
        with self.managed_session(db, commit_on_success=False) as session:
            query = session.query(BacktestHistoryModel)

            # Apply filters
            if user_id:
                query = query.filter(BacktestHistoryModel.user_id == user_id)
            if ticker:
                query = query.filter(BacktestHistoryModel.ticker == ticker)
            if strategy_name:
                query = query.filter(BacktestHistoryModel.strategy_name == strategy_name)
            if start_date:
                query = query.filter(BacktestHistoryModel.created_at >= start_date)
            if end_date:
                # Add one day to include the entire end date
                end_dt = datetime.fromisoformat(end_date) + timedelta(days=1)
                query = query.filter(BacktestHistoryModel.created_at < end_dt)

            # Get total count before pagination
            total = query.count()

            # Apply sorting
            sort_field = getattr(BacktestHistoryModel, sort_by, BacktestHistoryModel.created_at)
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_field))
            else:
                query = query.order_by(desc(sort_field))

            # Apply pagination
            query = query.offset(offset).limit(limit)

            # Execute query with error handling for corrupted JSON
            try:
                records = query.all()
            except Exception as e:
                logger.error(f"Failed to fetch backtest records due to data corruption: {e}")
                # If JSON deserialization fails, try to clean up corrupted records
                self._cleanup_corrupted_records(session)
                # Retry the query
                records = query.all()

            # Convert to dict format
            backtests = [self._record_to_dict(record) for record in records]

            return {"backtests": backtests, "total": total}

    def get_backtest(
        self,
        backtest_id: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get single backtest by ID."""
        with self.managed_session(db, commit_on_success=False) as session:
            query = session.query(BacktestHistoryModel).filter(
                BacktestHistoryModel.backtest_id == backtest_id
            )

            if user_id:
                query = query.filter(BacktestHistoryModel.user_id == user_id)

            record = query.first()

            if not record:
                return None

            return self._record_to_dict(record, include_full_metrics=True)

    def delete_backtest(
        self,
        backtest_id: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Delete backtest by ID and its associated plot file.

        Returns:
            True if deleted, False if not found
        """
        with self.managed_session(db) as session:
            try:
                query = session.query(BacktestHistoryModel).filter(
                    BacktestHistoryModel.backtest_id == backtest_id
                )

                if user_id:
                    query = query.filter(BacktestHistoryModel.user_id == user_id)

                record = query.first()

                if not record:
                    return False

                # Delete plot file if exists
                if record.plot_filename:
                    plot_path = IMAGES_DIR / record.plot_filename
                    if plot_path.exists():
                        try:
                            os.remove(plot_path)
                            logger.debug(f"Deleted plot file: {plot_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete plot {plot_path}: {e}")

                session.delete(record)

                logger.info(f"Deleted backtest {backtest_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to delete backtest {backtest_id}: {e}")
                return False

    def update_ai_analysis(
        self,
        backtest_id: str,
        model_name: str,
        analysis_content: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Update AI analysis for a backtest.
        Stores analysis in JSON format as: {model_name: analysis_content, ...}
        Multiple analyses from different models are preserved.

        Args:
            backtest_id: Backtest ID
            model_name: AI model name (e.g., "gpt-4o", "deepseek-v3.1")
            analysis_content: Analysis text content
            user_id: Optional user ID filter
            db: Optional database session

        Returns:
            True if updated, False if not found
        """
        with self.managed_session(db) as session:
            try:
                query = session.query(BacktestHistoryModel).filter(
                    BacktestHistoryModel.backtest_id == backtest_id
                )

                if user_id:
                    query = query.filter(BacktestHistoryModel.user_id == user_id)

                record = query.first()

                if not record:
                    return False

                # Get existing analyses or create new dict
                existing_analyses = record.ai_analysis if record.ai_analysis else {}

                # Update with new analysis for this model
                existing_analyses[model_name] = analysis_content

                record.ai_analysis = existing_analyses

                logger.info(f"Updated AI analysis ({model_name}) for backtest {backtest_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to update AI analysis for {backtest_id}: {e}")
                return False

    def update_deep_analysis(
        self,
        backtest_id: str,
        deep_analysis: Dict[str, Any],
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Save computed deep analysis to database.

        Args:
            backtest_id: Backtest ID
            deep_analysis: Deep analysis results dict
            user_id: Optional user ID filter
            db: Optional database session

        Returns:
            True if updated, False if not found
        """
        with self.managed_session(db) as session:
            try:
                query = session.query(BacktestHistoryModel).filter(
                    BacktestHistoryModel.backtest_id == backtest_id
                )

                if user_id:
                    query = query.filter(BacktestHistoryModel.user_id == user_id)

                record = query.first()

                if not record:
                    return False

                record.deep_analysis = deep_analysis

                logger.info(f"Updated deep analysis for backtest {backtest_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to update deep analysis for {backtest_id}: {e}")
                return False

    def get_deep_analysis(
        self,
        backtest_id: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached deep analysis for a backtest.

        Returns:
            Deep analysis dict if cached, None otherwise
        """
        with self.managed_session(db, commit_on_success=False) as session:
            query = session.query(BacktestHistoryModel).filter(
                BacktestHistoryModel.backtest_id == backtest_id
            )

            if user_id:
                query = query.filter(BacktestHistoryModel.user_id == user_id)

            record = query.first()

            if not record:
                return None

            return record.deep_analysis

    def _record_to_dict(
        self, record: BacktestHistoryModel, include_full_metrics: bool = False
    ) -> Dict[str, Any]:
        """Convert database record to dictionary."""
        result = {
            "backtest_id": record.backtest_id,
            "ticker": record.ticker,
            "start_date": record.start_date,
            "end_date": record.end_date,
            "initial_cash": record.initial_cash,
            "commission": record.commission,
            "stake": record.stake,
            "strategy_name": record.strategy_name,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "final_value": record.final_value,
            "total_return": record.total_return,
            "sharpe_ratio": record.sharpe_ratio,
            "max_drawdown": record.max_drawdown,
            "total_trades": record.total_trades,
            "winning_trades": record.winning_trades,
            "losing_trades": record.losing_trades,
            "plot_url": f"/images/{record.plot_filename}" if record.plot_filename else None,
        }

        if include_full_metrics:
            result["metrics"] = record.metrics if record.metrics is not None else {}
            result["chart_data"] = result["metrics"].get("chart_data")
            result["ai_analysis"] = record.ai_analysis if record.ai_analysis is not None else None
            result["strategy_code"] = record.strategy_code
            result["params"] = record.params if record.params is not None else None
            result["deep_analysis"] = record.deep_analysis if record.deep_analysis is not None else None

        return result
