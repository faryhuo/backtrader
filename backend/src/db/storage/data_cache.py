"""
Data Cache Storage - Manages market data cache with statistics, warmup, and cleanup.

Provides:
- Cache statistics (hit rate, ticker counts, date ranges)
- Batch data preheating
- Cache cleanup utilities
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.config.settings import DATABASE_URL
from src.db.models import MarketDataModel, init_database
from src.db.storage.base import BaseStorage

logger = logging.getLogger(__name__)


class DataCacheStorage(BaseStorage):
    """
    Market data cache management.
    
    Provides cache statistics, batch warmup, and cleanup operations.
    """

    def __init__(self, database_url: Optional[str] = None):
        """Initialize data cache storage."""
        super().__init__(database_url)
        logger.info("DataCacheStorage initialized")

    def get_cache_stats(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Get global cache statistics.
        
        Returns:
            Dict with cache statistics:
            - total_tickers: Number of cached tickers
            - total_records: Total OHLCV records
            - date_range: {start, end} of all cached data
            - tickers: List of ticker summaries
        """
        session, should_close = self._manage_session(db)
        
        try:
            # Get overall stats
            total_records = session.query(func.count(MarketDataModel.id)).scalar() or 0
            
            if total_records == 0:
                return {
                    "total_tickers": 0,
                    "total_records": 0,
                    "date_range": None,
                    "tickers": [],
                }
            
            # Get date range
            min_date = session.query(func.min(MarketDataModel.date)).scalar()
            max_date = session.query(func.max(MarketDataModel.date)).scalar()
            
            # Get per-ticker stats
            ticker_stats = (
                session.query(
                    MarketDataModel.ticker,
                    func.count(MarketDataModel.id).label("record_count"),
                    func.min(MarketDataModel.date).label("min_date"),
                    func.max(MarketDataModel.date).label("max_date"),
                    func.max(MarketDataModel.updated_at).label("last_updated"),
                )
                .group_by(MarketDataModel.ticker)
                .order_by(MarketDataModel.ticker)
                .all()
            )
            
            tickers = [
                {
                    "ticker": row.ticker,
                    "record_count": row.record_count,
                    "date_range": {
                        "start": row.min_date,
                        "end": row.max_date,
                    },
                    "last_updated": row.last_updated.isoformat() if row.last_updated else None,
                }
                for row in ticker_stats
            ]
            
            return {
                "total_tickers": len(tickers),
                "total_records": total_records,
                "date_range": {
                    "start": min_date,
                    "end": max_date,
                },
                "tickers": tickers,
            }
        
        finally:
            if should_close:
                session.close()

    def get_ticker_cache_info(
        self, ticker: str, db: Optional[Session] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cache information for a specific ticker.
        
        Args:
            ticker: Symbol ticker
            db: Optional database session
        
        Returns:
            Dict with ticker cache info, or None if not cached
        """
        session, should_close = self._manage_session(db)
        
        try:
            stats = (
                session.query(
                    func.count(MarketDataModel.id).label("record_count"),
                    func.min(MarketDataModel.date).label("min_date"),
                    func.max(MarketDataModel.date).label("max_date"),
                    func.min(MarketDataModel.created_at).label("first_cached"),
                    func.max(MarketDataModel.updated_at).label("last_updated"),
                )
                .filter(MarketDataModel.ticker == ticker)
                .first()
            )
            
            if not stats or stats.record_count == 0:
                return None
            
            # Get source info
            source = (
                session.query(MarketDataModel.source)
                .filter(MarketDataModel.ticker == ticker)
                .first()
            )
            
            return {
                "ticker": ticker,
                "record_count": stats.record_count,
                "date_range": {
                    "start": stats.min_date,
                    "end": stats.max_date,
                },
                "first_cached": stats.first_cached.isoformat() if stats.first_cached else None,
                "last_updated": stats.last_updated.isoformat() if stats.last_updated else None,
                "source": source[0] if source else "unknown",
            }
        
        finally:
            if should_close:
                session.close()

    def warmup_data(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Batch warmup data for multiple tickers.
        
        Args:
            tickers: List of ticker symbols to warmup
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            progress_callback: Optional callback (current_idx, total, ticker)
            db: Optional database session
        
        Returns:
            Dict with warmup results:
            - success: List of successful warmups
            - failed: List of failed warmups
            - cache_hits: Number of tickers already cached
            - cache_hit_rate: Ratio of cache hits
        """
        from src.db.storage.market_data import get_data, get_data_from_db
        
        session, should_close = self._manage_session(db)
        
        results = {
            "success": [],
            "failed": [],
            "cache_hits": 0,
            "total_fetched": 0,
        }
        
        total = len(tickers)
        
        try:
            for idx, ticker in enumerate(tickers):
                if progress_callback:
                    progress_callback(idx, total, ticker)
                
                try:
                    # Check if data is already cached
                    cached_data = get_data_from_db(ticker, start_date, end_date)
                    
                    if cached_data is not None and not cached_data.empty:
                        # Data exists in cache
                        expected_days = self._count_trading_days(start_date, end_date)
                        actual_days = len(cached_data)
                        coverage = actual_days / max(expected_days, 1)
                        
                        if coverage >= 0.9:  # 90% coverage = cache hit
                            results["success"].append({
                                "ticker": ticker,
                                "records": actual_days,
                                "from_cache": True,
                            })
                            results["cache_hits"] += 1
                            continue
                    
                    # Fetch from source (will auto-save to DB)
                    data = get_data(ticker, start_date, end_date)
                    records = len(data) if data is not None else 0
                    
                    results["success"].append({
                        "ticker": ticker,
                        "records": records,
                        "from_cache": False,
                    })
                    results["total_fetched"] += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to warmup {ticker}: {e}")
                    results["failed"].append({
                        "ticker": ticker,
                        "error": str(e),
                    })
            
            # Calculate cache hit rate
            successful = len(results["success"])
            results["cache_hit_rate"] = (
                results["cache_hits"] / total if total > 0 else 0.0
            )
            
            logger.info(
                f"Warmup complete: {successful}/{total} successful, "
                f"{results['cache_hits']} cache hits"
            )
            
            return results
        
        finally:
            if should_close:
                session.close()

    def cleanup_cache(
        self,
        before_date: Optional[str] = None,
        tickers: Optional[List[str]] = None,
        older_than_days: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, int]:
        """
        Clean up cached data.
        
        Args:
            before_date: Delete data before this date (YYYY-MM-DD)
            tickers: Only clean specified tickers (None = all)
            older_than_days: Delete data older than N days
            db: Optional database session
        
        Returns:
            Dict with cleanup results:
            - deleted_records: Number of deleted records
            - affected_tickers: Number of affected tickers
        """
        session, should_close = self._manage_session(db)
        
        try:
            query = session.query(MarketDataModel)
            
            # Apply date filter
            if before_date:
                query = query.filter(MarketDataModel.date < before_date)
            elif older_than_days:
                cutoff_date = (
                    datetime.now(timezone.utc) - timedelta(days=older_than_days)
                ).strftime("%Y-%m-%d")
                query = query.filter(MarketDataModel.date < cutoff_date)
            
            # Apply ticker filter
            if tickers:
                query = query.filter(MarketDataModel.ticker.in_(tickers))
            
            # Get affected tickers before deletion
            affected_query = (
                session.query(MarketDataModel.ticker)
                .filter(MarketDataModel.id.in_(query.with_entities(MarketDataModel.id)))
                .distinct()
            )
            affected_tickers = affected_query.count()
            
            # Perform deletion
            deleted_count = query.delete(synchronize_session="fetch")
            session.commit()
            
            logger.info(
                f"Cache cleanup: deleted {deleted_count} records "
                f"from {affected_tickers} tickers"
            )
            
            return {
                "deleted_records": deleted_count,
                "affected_tickers": affected_tickers,
            }
        
        except Exception as e:
            session.rollback()
            logger.error(f"Cache cleanup failed: {e}")
            raise
        
        finally:
            if should_close:
                session.close()

    def delete_ticker_cache(
        self, ticker: str, db: Optional[Session] = None
    ) -> bool:
        """
        Delete all cached data for a specific ticker.
        
        Args:
            ticker: Ticker symbol to delete
            db: Optional database session
        
        Returns:
            True if deleted, False if ticker not found
        """
        session, should_close = self._manage_session(db)
        
        try:
            deleted_count = (
                session.query(MarketDataModel)
                .filter(MarketDataModel.ticker == ticker)
                .delete(synchronize_session="fetch")
            )
            session.commit()
            
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} records for ticker {ticker}")
                return True
            
            return False
        
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete cache for {ticker}: {e}")
            raise
        
        finally:
            if should_close:
                session.close()

    def get_all_cached_tickers(self, db: Optional[Session] = None) -> List[str]:
        """
        Get list of all cached ticker symbols.
        
        Returns:
            List of ticker symbols
        """
        session, should_close = self._manage_session(db)
        
        try:
            tickers = (
                session.query(MarketDataModel.ticker)
                .distinct()
                .order_by(MarketDataModel.ticker)
                .all()
            )
            return [t[0] for t in tickers]
        
        finally:
            if should_close:
                session.close()

    def _count_trading_days(self, start_date: str, end_date: str) -> int:
        """
        Estimate number of trading days in date range.
        
        Uses simple heuristic: ~252 trading days per year.
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            calendar_days = (end - start).days + 1
            # Approx 5/7 days are trading days, minus holidays (~10/year)
            return max(1, int(calendar_days * 5 / 7 * 0.95))
        except Exception:
            return 252  # Default to 1 year


# Singleton instance
_data_cache_storage: Optional[DataCacheStorage] = None


def get_data_cache_storage() -> DataCacheStorage:
    """Get singleton instance of DataCacheStorage."""
    global _data_cache_storage
    if _data_cache_storage is None:
        _data_cache_storage = DataCacheStorage()
    return _data_cache_storage


__all__ = [
    "DataCacheStorage",
    "get_data_cache_storage",
]
