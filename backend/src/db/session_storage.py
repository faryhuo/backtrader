"""
Session Storage - Persistence layer for trading sessions.

This module provides database operations for saving and retrieving
trading sessions, orders, and positions.
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from src.db.models import (
    OrderModel,
    OrderStatusEnum,
    PositionModel,
    SessionStatusEnum,
    TradingSessionModel,
    init_database
)
from src.service.session_manager import SessionStatus, TradingSession

logger = logging.getLogger(__name__)


class SessionStorage:
    """
    Storage layer for trading sessions.

    Provides database operations for persisting and retrieving
    session data, supporting crash recovery and session history.
    """

    def __init__(self, database_url: str = "sqlite:///trading_sessions.db"):
        """
        Initialize session storage.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self._engine, self._SessionLocal = init_database(database_url)
        logger.info(f"SessionStorage initialized with database: {database_url}")

    def get_db_session(self) -> Session:
        """
        Get database session.

        Returns:
            SQLAlchemy session

        Usage:
            with storage.get_db_session() as db:
                # ... use db ...
        """
        return self._SessionLocal()

    def save_session(self, session: TradingSession, db: Optional[Session] = None) -> None:
        """
        Save or update trading session in database.

        Args:
            session: TradingSession to save
            db: Optional database session (creates new if None)
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            # Check if session exists
            existing = db.query(TradingSessionModel).filter(
                TradingSessionModel.session_id == session.session_id
            ).first()

            if existing:
                # Update existing
                existing.status = SessionStatusEnum[session.status.name]
                existing.end_time = session.end_time
                existing.total_pnl = session.current_pnl
                existing.total_trades = session.total_trades
                existing.positions = session.positions
                existing.error_message = session.error_message
                existing.updated_at = datetime.utcnow()

                logger.debug(f"Updated session {session.session_id} in database")

            else:
                # Create new
                db_session = TradingSessionModel(
                    session_id=session.session_id,
                    strategy_name=session.strategy_name,
                    symbol=session.symbol,
                    exchange=session.exchange,
                    mode=session.mode,
                    timeframe=session.timeframe,
                    status=SessionStatusEnum[session.status.name],
                    start_time=session.start_time,
                    end_time=session.end_time,
                    initial_cash=session.initial_cash,
                    commission=session.commission,
                    total_pnl=session.current_pnl,
                    total_trades=session.total_trades,
                    positions=session.positions,
                    error_message=session.error_message
                )

                db.add(db_session)
                logger.debug(f"Created session {session.session_id} in database")

            db.commit()

        except Exception as e:
            logger.error(f"Failed to save session {session.session_id}: {e}")
            db.rollback()
            raise

        finally:
            if close_db:
                db.close()

    def load_session(self, session_id: str, db: Optional[Session] = None) -> Optional[TradingSession]:
        """
        Load trading session from database.

        Args:
            session_id: Session ID to load
            db: Optional database session

        Returns:
            TradingSession if found, None otherwise
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            db_session = db.query(TradingSessionModel).filter(
                TradingSessionModel.session_id == session_id
            ).first()

            if not db_session:
                return None

            # Convert database model to TradingSession
            session = TradingSession(
                session_id=db_session.session_id,
                strategy_name=db_session.strategy_name,
                symbol=db_session.symbol,
                exchange=db_session.exchange,
                mode=db_session.mode,
                timeframe=db_session.timeframe,
                initial_cash=db_session.initial_cash,
                commission=db_session.commission,
                status=SessionStatus[db_session.status.name],
                start_time=db_session.start_time,
                end_time=db_session.end_time,
                current_pnl=db_session.total_pnl,
                total_trades=db_session.total_trades,
                positions=db_session.positions or [],
                orders=[]  # Orders loaded separately if needed
            )

            return session

        finally:
            if close_db:
                db.close()

    def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
        limit: int = 100,
        offset: int = 0,
        db: Optional[Session] = None
    ) -> List[TradingSession]:
        """
        List trading sessions from database.

        Args:
            status: Filter by status
            limit: Maximum number of results
            offset: Offset for pagination
            db: Optional database session

        Returns:
            List of TradingSessions
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            query = db.query(TradingSessionModel).order_by(
                TradingSessionModel.start_time.desc()
            )

            if status:
                query = query.filter(
                    TradingSessionModel.status == SessionStatusEnum[status.name]
                )

            query = query.offset(offset).limit(limit)

            sessions = []
            for db_session in query.all():
                session = TradingSession(
                    session_id=db_session.session_id,
                    strategy_name=db_session.strategy_name,
                    symbol=db_session.symbol,
                    exchange=db_session.exchange,
                    mode=db_session.mode,
                    timeframe=db_session.timeframe,
                    initial_cash=db_session.initial_cash,
                    commission=db_session.commission,
                    status=SessionStatus[db_session.status.name],
                    start_time=db_session.start_time,
                    end_time=db_session.end_time,
                    current_pnl=db_session.total_pnl,
                    total_trades=db_session.total_trades,
                    positions=db_session.positions or []
                )
                sessions.append(session)

            return sessions

        finally:
            if close_db:
                db.close()

    def delete_session(self, session_id: str, db: Optional[Session] = None) -> bool:
        """
        Delete session from database.

        Args:
            session_id: Session to delete
            db: Optional database session

        Returns:
            bool: True if deleted, False if not found
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            result = db.query(TradingSessionModel).filter(
                TradingSessionModel.session_id == session_id
            ).delete()

            db.commit()

            return result > 0

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            db.rollback()
            return False

        finally:
            if close_db:
                db.close()

    def save_order(self, order_dict: dict, db: Optional[Session] = None) -> None:
        """
        Save order to database.

        Args:
            order_dict: Order data dictionary
            db: Optional database session
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            order = OrderModel(
                order_id=order_dict['order_id'],
                session_id=order_dict['session_id'],
                exchange_order_id=order_dict.get('exchange_order_id'),
                symbol=order_dict['symbol'],
                side=order_dict['side'],
                type=order_dict['type'],
                size=order_dict['size'],
                price=order_dict.get('price'),
                status=OrderStatusEnum[order_dict['status'].upper()],
                filled_size=order_dict.get('filled_size', 0),
                filled_price=order_dict.get('filled_price'),
                commission=order_dict.get('commission', 0),
                cost=order_dict.get('cost'),
                pnl=order_dict.get('pnl')
            )

            db.add(order)
            db.commit()

            logger.debug(f"Saved order {order_dict['order_id']} to database")

        except Exception as e:
            logger.error(f"Failed to save order: {e}")
            db.rollback()
            raise

        finally:
            if close_db:
                db.close()

    def get_session_orders(
        self,
        session_id: str,
        db: Optional[Session] = None
    ) -> List[dict]:
        """
        Get all orders for a session.

        Args:
            session_id: Session ID
            db: Optional database session

        Returns:
            List of order dictionaries
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            orders = db.query(OrderModel).filter(
                OrderModel.session_id == session_id
            ).order_by(OrderModel.created_at).all()

            return [
                {
                    'order_id': o.order_id,
                    'exchange_order_id': o.exchange_order_id,
                    'symbol': o.symbol,
                    'side': o.side,
                    'type': o.type,
                    'size': o.size,
                    'price': o.price,
                    'status': o.status.value,
                    'filled_size': o.filled_size,
                    'filled_price': o.filled_price,
                    'commission': o.commission,
                    'created_at': o.created_at.isoformat()
                }
                for o in orders
            ]

        finally:
            if close_db:
                db.close()

    def get_session_count(self, db: Optional[Session] = None) -> dict:
        """
        Get count of sessions by status.

        Args:
            db: Optional database session

        Returns:
            dict: {status: count}
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            counts = {}

            for status in SessionStatusEnum:
                count = db.query(TradingSessionModel).filter(
                    TradingSessionModel.status == status
                ).count()
                counts[status.value] = count

            counts['total'] = db.query(TradingSessionModel).count()

            return counts

        finally:
            if close_db:
                db.close()
