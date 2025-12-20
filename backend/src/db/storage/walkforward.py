"""
Walk-Forward Optimization Storage - Persistence layer for optimization results.

Provides database operations for saving and retrieving walk-forward analysis results.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from src.config.settings import DATABASE_URL
from src.db.storage.base import BaseStorage
from src.db.models import WalkForwardOptimizationModel, init_database
from src.service.walkforward_optimizer import WalkForwardResult
from src.service.parameter_analysis import get_parameter_analysis

logger = logging.getLogger(__name__)


class WalkForwardStorage(BaseStorage):
    """Storage layer for walk-forward optimization results."""

    def __init__(self, database_url: str = "sqlite:///trading_sessions.db"):
        """Initialize walk-forward storage."""
        super().__init__(database_url)
        logger.info(f"WalkForwardStorage initialized with database: {self.database_url}")

    def create_optimization(
        self,
        optimization_id: str,
        strategy_name: str,
        ticker: str,
        start_date: str,
        end_date: str,
        param_grid: Dict[str, List[Any]],
        train_period_days: int,
        test_period_days: int,
        anchored: bool,
        optimization_metric: str,
        initial_cash: float,
        commission: float,
        stake: int,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> WalkForwardOptimizationModel:
        """
        Create a new walk-forward optimization record (status: pending).

        Args:
            optimization_id: Unique identifier (UUID)
            strategy_name: Strategy name
            ticker: Symbol
            start_date: Overall start date
            end_date: Overall end date
            param_grid: Parameter grid to optimize
            train_period_days: Training window size
            test_period_days: Test window size
            anchored: Anchored vs rolling window
            optimization_metric: Metric to optimize
            initial_cash: Initial cash
            commission: Commission rate
            stake: Position size
            user_id: Optional user identifier
            db: Optional database session

        Returns:
            Created WalkForwardOptimizationModel instance
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            record = WalkForwardOptimizationModel(
                optimization_id=optimization_id,
                user_id=user_id,
                strategy_name=strategy_name,
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                train_period_days=train_period_days,
                test_period_days=test_period_days,
                anchored=1 if anchored else 0,
                optimization_metric=optimization_metric,
                initial_cash=initial_cash,
                commission=commission,
                stake=stake,
                param_grid=param_grid,
                status="pending",
                created_at=datetime.utcnow(),
            )

            db.add(record)
            db.commit()
            db.refresh(record)

            logger.info(f"Created walk-forward optimization {optimization_id}")
            return record

        except Exception as e:
            logger.error(f"Failed to create optimization {optimization_id}: {e}")
            db.rollback()
            raise
        finally:
            if close_db:
                db.close()

    def update_optimization_status(
        self,
        optimization_id: str,
        status: str,
        error_message: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Update optimization status.

        Args:
            optimization_id: Optimization ID
            status: New status (pending, running, completed, failed)
            error_message: Optional error message
            db: Optional database session

        Returns:
            True if updated, False if not found
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            record = db.query(WalkForwardOptimizationModel).filter(
                WalkForwardOptimizationModel.optimization_id == optimization_id
            ).first()

            if not record:
                return False

            record.status = status
            if error_message:
                record.error_message = error_message
            if status == "completed":
                record.completed_at = datetime.utcnow()

            db.commit()
            logger.info(f"Updated optimization {optimization_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to update status for {optimization_id}: {e}")
            db.rollback()
            return False
        finally:
            if close_db:
                db.close()

    def save_optimization_result(
        self,
        result: WalkForwardResult,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> WalkForwardOptimizationModel:
        """
        Save complete walk-forward optimization result.

        Args:
            result: WalkForwardResult instance
            user_id: Optional user identifier
            db: Optional database session

        Returns:
            Updated WalkForwardOptimizationModel instance
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            record = db.query(WalkForwardOptimizationModel).filter(
                WalkForwardOptimizationModel.optimization_id == result.optimization_id
            ).first()

            if not record:
                raise ValueError(f"Optimization {result.optimization_id} not found")

            # Convert windows to serializable format
            windows_data = []
            for window in result.windows:
                windows_data.append({
                    "window_id": window.window_id,
                    "train_start": window.train_start,
                    "train_end": window.train_end,
                    "test_start": window.test_start,
                    "test_end": window.test_end,
                    "best_params": window.best_params,
                    "train_metrics": window.train_metrics,
                    "test_metrics": window.test_metrics,
                    "all_train_results": window.all_train_results,
                })

            # Update record with results
            record.status = "completed"
            record.completed_at = datetime.utcnow()
            record.num_windows = len(result.windows)
            record.windows = windows_data
            record.overfitting_metrics = result.overfitting_metrics
            record.combined_test_metrics = result.combined_test_metrics

            # Update denormalized summary fields
            record.avg_train_performance = result.overfitting_metrics.get("avg_train_performance")
            record.avg_test_performance = result.overfitting_metrics.get("avg_test_performance")
            record.avg_degradation_pct = result.overfitting_metrics.get("avg_degradation_pct")
            record.train_test_correlation = result.overfitting_metrics.get("train_test_correlation")
            record.consistency_score = result.overfitting_metrics.get("consistency_score")
            record.overfitting_detected = 1 if result.overfitting_metrics.get("overfitting_detected") else 0

            db.commit()
            db.refresh(record)

            logger.info(f"Saved walk-forward optimization result {result.optimization_id}")
            return record

        except Exception as e:
            logger.error(f"Failed to save optimization result {result.optimization_id}: {e}")
            db.rollback()
            raise
        finally:
            if close_db:
                db.close()

    def list_optimizations(
        self,
        ticker: Optional[str] = None,
        strategy_name: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        List walk-forward optimizations with filtering and sorting.

        Args:
            ticker: Filter by ticker symbol
            strategy_name: Filter by strategy name
            status: Filter by status
            sort_by: Field to sort by
            sort_order: "asc" or "desc"
            limit: Max records to return
            offset: Pagination offset
            user_id: Filter by user ID
            db: Optional database session

        Returns:
            Dict with 'optimizations' list and 'total' count
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            query = db.query(WalkForwardOptimizationModel)

            # Apply filters
            if user_id:
                query = query.filter(WalkForwardOptimizationModel.user_id == user_id)
            if ticker:
                query = query.filter(WalkForwardOptimizationModel.ticker == ticker)
            if strategy_name:
                query = query.filter(WalkForwardOptimizationModel.strategy_name == strategy_name)
            if status:
                query = query.filter(WalkForwardOptimizationModel.status == status)

            # Get total count before pagination
            total = query.count()

            # Apply sorting
            sort_field = getattr(WalkForwardOptimizationModel, sort_by, WalkForwardOptimizationModel.created_at)
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_field))
            else:
                query = query.order_by(desc(sort_field))

            # Apply pagination
            query = query.offset(offset).limit(limit)

            records = query.all()

            # Convert to dict format
            optimizations = [self._record_to_dict(record) for record in records]

            return {"optimizations": optimizations, "total": total}

        finally:
            if close_db:
                db.close()

    def get_optimization(
        self,
        optimization_id: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get single optimization by ID."""
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            query = db.query(WalkForwardOptimizationModel).filter(
                WalkForwardOptimizationModel.optimization_id == optimization_id
            )

            if user_id:
                query = query.filter(WalkForwardOptimizationModel.user_id == user_id)

            record = query.first()

            if not record:
                return None

            return self._record_to_dict(record, include_full_results=True)

        finally:
            if close_db:
                db.close()

    def delete_optimization(
        self,
        optimization_id: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Delete optimization by ID.

        Returns:
            True if deleted, False if not found
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            query = db.query(WalkForwardOptimizationModel).filter(
                WalkForwardOptimizationModel.optimization_id == optimization_id
            )

            if user_id:
                query = query.filter(WalkForwardOptimizationModel.user_id == user_id)

            record = query.first()

            if not record:
                return False

            db.delete(record)
            db.commit()

            logger.info(f"Deleted optimization {optimization_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete optimization {optimization_id}: {e}")
            db.rollback()
            return False
        finally:
            if close_db:
                db.close()

    def _record_to_dict(
        self,
        record: WalkForwardOptimizationModel,
        include_full_results: bool = False,
    ) -> Dict[str, Any]:
        """Convert database record to dictionary."""
        result = {
            "optimization_id": record.optimization_id,
            "strategy_name": record.strategy_name,
            "ticker": record.ticker,
            "start_date": record.start_date,
            "end_date": record.end_date,
            "train_period_days": record.train_period_days,
            "test_period_days": record.test_period_days,
            "anchored": bool(record.anchored),
            "optimization_metric": record.optimization_metric,
            "initial_cash": record.initial_cash,
            "commission": record.commission,
            "stake": record.stake,
            "param_grid": record.param_grid,
            "status": record.status,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
            "num_windows": record.num_windows,
            "avg_train_performance": record.avg_train_performance,
            "avg_test_performance": record.avg_test_performance,
            "avg_degradation_pct": record.avg_degradation_pct,
            "train_test_correlation": record.train_test_correlation,
            "consistency_score": record.consistency_score,
            "overfitting_detected": bool(record.overfitting_detected),
            "error_message": record.error_message,
        }

        if include_full_results:
            windows = record.windows if record.windows is not None else []
            overfitting_metrics = record.overfitting_metrics if record.overfitting_metrics is not None else {}
            
            result["windows"] = windows
            result["overfitting_metrics"] = overfitting_metrics
            result["combined_test_metrics"] = record.combined_test_metrics if record.combined_test_metrics is not None else {}
            
            # Compute parameter analysis on-demand from windows data
            try:
                result["parameter_analysis"] = get_parameter_analysis(
                    windows=windows,
                    param_grid=record.param_grid or {},
                    optimization_metric=record.optimization_metric or "sharpe_ratio",
                    overfitting_metrics=overfitting_metrics,
                )
            except Exception as e:
                logger.warning(f"Failed to compute parameter analysis: {e}")
                result["parameter_analysis"] = {}

        return result


__all__ = ["WalkForwardStorage"]
