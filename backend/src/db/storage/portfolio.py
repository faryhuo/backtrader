"""
Portfolio Storage - CRUD operations for portfolio backtest results.

This module provides database operations for storing and retrieving
multi-asset portfolio backtest results.
"""

import logging
from datetime import datetime
from typing import Optional

from src.config.settings import DATABASE_URL, DEFAULT_DB_URL
from src.db.storage.base import BaseStorage
from src.db.models import PortfolioResultModel, init_database

logger = logging.getLogger(__name__)

# Use default local database if DATABASE_URL is not configured
_DB_URL = DATABASE_URL or DEFAULT_DB_URL


class PortfolioStorage(BaseStorage):
    """Storage class for portfolio backtest results."""

    def __init__(self, database_url: str = None):
        """Initialize storage with database connection."""
        super().__init__(database_url or _DB_URL)

    def _get_session(self):
        """Get database session (alias for backward compatibility)."""
        return self.get_db_session()

    def save_result(self, result: dict, user_id: Optional[str] = None) -> str:
        """
        Save a portfolio backtest result to the database.

        Args:
            result: Portfolio backtest result dict from run_portfolio_backtest()
            user_id: Optional user ID for multi-user support

        Returns:
            str: Portfolio ID of saved result
        """
        session = self._get_session()
        try:
            portfolio_metrics = result.get("portfolio_metrics", {})
            
            model = PortfolioResultModel(
                portfolio_id=result.get("id"),
                user_id=user_id,
                tickers=result.get("tickers", []),
                weights=result.get("weights", []),
                start_date=result.get("start_date"),
                end_date=result.get("end_date"),
                initial_cash=portfolio_metrics.get("initial_cash", 0),
                commission=portfolio_metrics.get("commission", 0.0005),
                strategy_name=result.get("strategy_name"),
                final_value=portfolio_metrics.get("final_value"),
                total_return=portfolio_metrics.get("total_return"),
                weighted_sharpe=portfolio_metrics.get("weighted_sharpe"),
                max_drawdown=portfolio_metrics.get("max_drawdown"),
                num_assets=portfolio_metrics.get("num_assets", 0),
                successful_backtests=portfolio_metrics.get("successful_backtests", 0),
                failed_backtests=portfolio_metrics.get("failed_backtests", 0),
                portfolio_metrics=portfolio_metrics,
                individual_results=result.get("individual_results", []),
                correlation_matrix=result.get("correlation", {}),
                optimization_suggestion=result.get("optimization", {}),
                plot_filename=result.get("plot_filename"),
                params=result.get("params"),
            )

            session.add(model)
            session.commit()
            logger.info(f"Saved portfolio result {model.portfolio_id}")
            return model.portfolio_id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save portfolio result: {e}")
            raise
        finally:
            session.close()

    def get_by_id(self, portfolio_id: str, user_id: Optional[str] = None) -> Optional[dict]:
        """
        Get a portfolio result by ID.

        Args:
            portfolio_id: Portfolio ID
            user_id: Optional user ID for filtering

        Returns:
            dict or None: Portfolio result dict
        """
        session = self._get_session()
        try:
            query = session.query(PortfolioResultModel).filter(
                PortfolioResultModel.portfolio_id == portfolio_id
            )
            if user_id:
                query = query.filter(PortfolioResultModel.user_id == user_id)
            
            model = query.first()
            if not model:
                return None
            
            return self._model_to_dict(model)
        finally:
            session.close()

    def list_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> list[dict]:
        """
        List portfolio backtest history.

        Args:
            user_id: Optional user ID for filtering
            limit: Max records to return
            offset: Records to skip
            sort_by: Column to sort by
            sort_order: 'asc' or 'desc'

        Returns:
            list: List of portfolio result dicts
        """
        session = self._get_session()
        try:
            query = session.query(PortfolioResultModel)
            
            if user_id:
                query = query.filter(PortfolioResultModel.user_id == user_id)
            
            # Apply sorting
            sort_column = getattr(PortfolioResultModel, sort_by, PortfolioResultModel.created_at)
            if sort_order.lower() == "asc":
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            results = []
            for model in query.all():
                results.append(self._model_to_dict(model, summary=True))
            
            return results
        finally:
            session.close()

    def delete_by_id(self, portfolio_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a portfolio result by ID.

        Args:
            portfolio_id: Portfolio ID to delete
            user_id: Optional user ID for filtering

        Returns:
            bool: True if deleted, False if not found
        """
        session = self._get_session()
        try:
            query = session.query(PortfolioResultModel).filter(
                PortfolioResultModel.portfolio_id == portfolio_id
            )
            if user_id:
                query = query.filter(PortfolioResultModel.user_id == user_id)
            
            model = query.first()
            if not model:
                return False
            
            session.delete(model)
            session.commit()
            logger.info(f"Deleted portfolio result {portfolio_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete portfolio result: {e}")
            raise
        finally:
            session.close()

    def _model_to_dict(self, model: PortfolioResultModel, summary: bool = False) -> dict:
        """Convert model to dict."""
        result = {
            "id": model.portfolio_id,
            "portfolio_id": model.portfolio_id,  # Also include for frontend compatibility
            "user_id": model.user_id,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "tickers": model.tickers,
            "weights": model.weights,
            "start_date": model.start_date,
            "end_date": model.end_date,
            "initial_cash": model.initial_cash,
            "commission": model.commission,
            "strategy_name": model.strategy_name,
            "final_value": model.final_value,
            "total_return": model.total_return,
            "weighted_sharpe": model.weighted_sharpe,
            "max_drawdown": model.max_drawdown,
            "num_assets": model.num_assets,
            "successful_backtests": model.successful_backtests,
            "failed_backtests": model.failed_backtests,
            "plot_filename": model.plot_filename,
        }
        
        if not summary:
            result.update({
                "portfolio_metrics": model.portfolio_metrics,
                "individual_results": model.individual_results,
                "correlation": model.correlation_matrix,
                "optimization": model.optimization_suggestion,
            })
        
        return result


# Singleton instance for convenience
_storage_instance = None


def get_portfolio_storage() -> PortfolioStorage:
    """Get or create portfolio storage singleton."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = PortfolioStorage()
    return _storage_instance
