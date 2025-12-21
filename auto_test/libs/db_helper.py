"""
Database Helper Utilities

Provides utilities for:
- Database connection management
- Test data seeding
- Data cleanup
- Query helpers
"""

import os
import sqlite3
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class DBHelper:
    """Database helper for test setup and teardown."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database helper.

        Args:
            db_path: Path to database file (defaults to env var TEST_DB_PATH)
        """
        self.db_path = db_path or os.getenv(
            "TEST_DB_PATH",
            "d:/Project/backtrader/backend/trading_sessions.db"
        )

    @contextmanager
    def get_connection(self):
        """
        Get database connection context manager.

        Yields:
            sqlite3.Connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of row dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results

    def execute_update(
        self,
        query: str,
        params: Optional[tuple] = None,
    ) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount

    def delete_backtest_by_id(self, backtest_id: str) -> bool:
        """
        Delete a backtest record by ID.

        Args:
            backtest_id: Backtest UUID

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM backtest_history WHERE backtest_id = ?"
        rows = self.execute_update(query, (backtest_id,))
        return rows > 0

    def delete_all_backtests(self):
        """Delete all backtest records."""
        self.execute_update("DELETE FROM backtest_history")

    def delete_strategy_by_name(self, strategy_name: str) -> bool:
        """
        Delete a strategy by name.

        Args:
            strategy_name: Strategy name

        Returns:
            True if deleted, False if not found
        """
        # Note: Strategies are file-based, not in DB
        # This is a placeholder for future DB-based storage
        pass

    def get_backtest_count(self) -> int:
        """
        Get total number of backtests.

        Returns:
            Count of backtest records
        """
        result = self.execute_query("SELECT COUNT(*) as count FROM backtest_history")
        return result[0]["count"] if result else 0

    def get_backtest_by_id(self, backtest_id: str) -> Optional[Dict[str, Any]]:
        """
        Get backtest record by ID.

        Args:
            backtest_id: Backtest UUID

        Returns:
            Backtest record or None
        """
        query = "SELECT * FROM backtest_history WHERE backtest_id = ?"
        results = self.execute_query(query, (backtest_id,))
        return results[0] if results else None

    def cleanup_test_data(self, user_id: Optional[str] = None):
        """
        Clean up test data from database.

        Args:
            user_id: If provided, only clean data for this user
        """
        if user_id:
            # Clean backtests for specific user
            self.execute_update(
                "DELETE FROM backtest_history WHERE user_id = ?",
                (user_id,)
            )
            # Clean other user-specific data as needed
        else:
            # Clean all test data
            self.delete_all_backtests()
            # Add other cleanup as needed

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists.

        Args:
            table_name: Table name

        Returns:
            True if table exists
        """
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        results = self.execute_query(query, (table_name,))
        return len(results) > 0

    def get_table_row_count(self, table_name: str) -> int:
        """
        Get row count for a table.

        Args:
            table_name: Table name

        Returns:
            Number of rows
        """
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result[0]["count"] if result else 0
