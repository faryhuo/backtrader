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

    def save_result(self, result: dict, user_id: Optional[str] = None) -> str:
        """
        Save a portfolio backtest result to the database.

        Args:
            result: Portfolio backtest result dict from run_multi_asset_backtest()
            user_id: Optional user ID for multi-user support

        Returns:
            str: Portfolio ID of saved result
        """
        with self.managed_session() as session:
            try:
                portfolio_metrics = result.get("portfolio_metrics", {})
                
                # Include optimization and correlation in portfolio_metrics for storage
                if result.get("optimization"):
                    portfolio_metrics["optimization"] = result.get("optimization")
                if result.get("correlation"):
                    portfolio_metrics["correlation"] = result.get("correlation")
                
                model = PortfolioResultModel(
                    portfolio_id=result.get("id"),
                    user_id=user_id,
                    tickers=result.get("tickers", []),
                    weights=result.get("weights", []),
                    start_date=result.get("start_date"),
                    end_date=result.get("end_date"),
                    initial_cash=result.get("initial_cash") or portfolio_metrics.get("initial_cash", 0),
                    commission=result.get("commission") or portfolio_metrics.get("commission", 0.0005),
                    strategy_name=result.get("strategy_name"),
                    final_value=result.get("final_value") or portfolio_metrics.get("final_value"),
                    total_return=result.get("total_return") or portfolio_metrics.get("total_return"),
                    weighted_sharpe=result.get("weighted_sharpe") or portfolio_metrics.get("weighted_sharpe"),
                    max_drawdown=result.get("max_drawdown") or portfolio_metrics.get("max_drawdown"),
                    num_assets=result.get("num_assets") or portfolio_metrics.get("num_assets", 0),
                    successful_backtests=portfolio_metrics.get("successful_backtests", 0),
                    failed_backtests=portfolio_metrics.get("failed_backtests", 0),
                    portfolio_metrics=portfolio_metrics,
                    individual_results=result.get("individual_results", []),
                    plot_filename=result.get("plot_filename"),
                    # Multi-asset specific fields
                    equity_curve=result.get("equity_curve", {}),
                    asset_contributions=result.get("asset_contributions", {}),
                    all_trades=result.get("all_trades", []),
                )

                session.add(model)
                session.flush()
                logger.info(f"Saved portfolio result {model.portfolio_id}")
                return model.portfolio_id
            except Exception as e:
                logger.error(f"Failed to save portfolio result: {e}")
                raise

    def get_by_id(self, portfolio_id: str, user_id: Optional[str] = None) -> Optional[dict]:
        """
        Get a portfolio result by ID.

        Args:
            portfolio_id: Portfolio ID
            user_id: Optional user ID for filtering

        Returns:
            dict or None: Portfolio result dict
        """
        with self.managed_session(commit_on_success=False) as session:
            query = session.query(PortfolioResultModel).filter(
                PortfolioResultModel.portfolio_id == portfolio_id
            )
            if user_id:
                query = query.filter(PortfolioResultModel.user_id == user_id)
            
            model = query.first()
            if not model:
                return None
            
            return self._model_to_dict(model)

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
        with self.managed_session(commit_on_success=False) as session:
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

    def delete_by_id(self, portfolio_id: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a portfolio result by ID.

        Args:
            portfolio_id: Portfolio ID to delete
            user_id: Optional user ID for filtering

        Returns:
            bool: True if deleted, False if not found
        """
        with self.managed_session() as session:
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
                logger.info(f"Deleted portfolio result {portfolio_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete portfolio result: {e}")
                raise

    def _model_to_dict(self, model: PortfolioResultModel, summary: bool = False) -> dict:
        """Convert model to dict with proper structure for frontend."""
        portfolio_metrics = model.portfolio_metrics or {}
        
        # Extract metrics from portfolio_metrics JSON
        sharpe_ratio = model.weighted_sharpe or portfolio_metrics.get("sharpe_ratio")
        calmar_ratio = portfolio_metrics.get("calmar_ratio")
        recovery_factor = portfolio_metrics.get("recovery_factor")
        total_commission = portfolio_metrics.get("total_commission", 0.0)
        total_volume = portfolio_metrics.get("total_volume", 0.0)
        total_trades = portfolio_metrics.get("total_trades", 0)
        
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
            "plot_url": f"/images/{model.plot_filename}" if model.plot_filename else None,
            # Risk-adjusted metrics at root level for frontend compatibility
            "sharpe_ratio": sharpe_ratio,
            "calmar_ratio": calmar_ratio,
            "recovery_factor": recovery_factor,
            # Trading activity at root level
            "total_commission": total_commission,
            "total_volume": total_volume,
            "total_trades": total_trades,
        }
        
        if not summary:
            # Extract optimization and correlation from portfolio_metrics
            optimization = portfolio_metrics.get("optimization")
            correlation = portfolio_metrics.get("correlation")
            
            result.update({
                "portfolio_metrics": portfolio_metrics,
                "individual_results": model.individual_results,
                # Multi-asset specific fields
                "equity_curve": model.equity_curve or {},
                "asset_contributions": model.asset_contributions or {},
                "all_trades": model.all_trades or [],
                # Wrap in metrics structure for frontend compatibility
                "metrics": {
                    "portfolio_metrics": portfolio_metrics.get("portfolio_metrics", portfolio_metrics),
                    "returns": portfolio_metrics.get("returns", {}),
                    "drawdown": portfolio_metrics.get("drawdown", {}),
                },
                # Optimization suggestions
                "optimization": optimization,
                # Correlation matrix
                "correlation": correlation,
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
