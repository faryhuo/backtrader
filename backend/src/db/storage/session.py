"""
Session Storage - Persistence layer for trading sessions.

This module provides database operations for saving and retrieving
trading sessions, orders, and positions.
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from src.config.settings import DATABASE_URL
from src.db.storage.base import BaseStorage
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


def build_session_order_pk(session_id: str, order_id: str) -> str:
    """Build a database-safe order primary key scoped by session."""
    return f"{session_id}:{order_id}"


def extract_client_order_id(order: OrderModel) -> str:
    """Return the original client-visible order id from stored order data."""
    metadata = order.metadata_json or {}
    client_order_id = metadata.get('client_order_id')
    if client_order_id:
        return str(client_order_id)

    prefix = f"{order.session_id}:"
    if order.order_id.startswith(prefix):
        return order.order_id[len(prefix):]

    return order.order_id


class SessionStorage(BaseStorage):
    """
    Storage layer for trading sessions.

    Provides database operations for persisting and retrieving
    session data, supporting crash recovery and session history.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize session storage.

        Args:
            database_url: SQLAlchemy database URL (defaults to DATABASE_URL from settings)
        """
        super().__init__(database_url)
        logger.info(f"SessionStorage initialized with database: {self.database_url}")

    def save_session(self, session: TradingSession, db: Optional[Session] = None) -> None:
        """
        Save or update trading session in database.

        Args:
            session: TradingSession to save
            db: Optional database session (creates new if None)
        """
        with self.managed_session(db) as db_session:
            try:
                # Check if session exists
                existing = db_session.query(TradingSessionModel).filter(
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
                    existing.config = {
                        **(existing.config or {}),
                        'market': session.market,
                    }
                    existing.updated_at = datetime.utcnow()

                    logger.debug(f"Updated session {session.session_id} in database")

                else:
                    # Create new
                    new_session = TradingSessionModel(
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
                        config={'market': session.market},
                        error_message=session.error_message
                    )

                    db_session.add(new_session)
                    logger.debug(f"Created session {session.session_id} in database")

            except Exception as e:
                logger.error(f"Failed to save session {session.session_id}: {e}")
                raise

    def load_session(self, session_id: str, db: Optional[Session] = None) -> Optional[TradingSession]:
        """
        Load trading session from database.

        Args:
            session_id: Session ID to load
            db: Optional database session

        Returns:
            TradingSession if found, None otherwise
        """
        with self.managed_session(db, commit_on_success=False) as db_session:
            db_record = db_session.query(TradingSessionModel).filter(
                TradingSessionModel.session_id == session_id
            ).first()

            if not db_record:
                return None

            # Convert database model to TradingSession
            session = TradingSession(
                session_id=db_record.session_id,
                strategy_name=db_record.strategy_name,
                symbol=db_record.symbol,
                exchange=db_record.exchange,
                market=(db_record.config or {}).get('market', 'spot'),
                mode=db_record.mode,
                timeframe=db_record.timeframe,
                initial_cash=db_record.initial_cash,
                commission=db_record.commission,
                status=SessionStatus[db_record.status.name],
                start_time=db_record.start_time,
                end_time=db_record.end_time,
                current_pnl=db_record.total_pnl,
                total_trades=db_record.total_trades,
                positions=db_record.positions or [],
                orders=[]  # Orders loaded separately if needed
            )

            return session

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
        with self.managed_session(db, commit_on_success=False) as db_session:
            query = db_session.query(TradingSessionModel).order_by(
                TradingSessionModel.start_time.desc()
            )

            if status:
                query = query.filter(
                    TradingSessionModel.status == SessionStatusEnum[status.name]
                )

            query = query.offset(offset).limit(limit)

            sessions = []
            for db_record in query.all():
                session = TradingSession(
                    session_id=db_record.session_id,
                    strategy_name=db_record.strategy_name,
                    symbol=db_record.symbol,
                    exchange=db_record.exchange,
                    market=(db_record.config or {}).get('market', 'spot'),
                    mode=db_record.mode,
                    timeframe=db_record.timeframe,
                    initial_cash=db_record.initial_cash,
                    commission=db_record.commission,
                    status=SessionStatus[db_record.status.name],
                    start_time=db_record.start_time,
                    end_time=db_record.end_time,
                    current_pnl=db_record.total_pnl,
                    total_trades=db_record.total_trades,
                    positions=db_record.positions or []
                )
                sessions.append(session)

            return sessions

    def delete_session(self, session_id: str, db: Optional[Session] = None) -> bool:
        """
        Delete session from database.

        Args:
            session_id: Session to delete
            db: Optional database session

        Returns:
            bool: True if deleted, False if not found
        """
        with self.managed_session(db) as db_session:
            try:
                result = db_session.query(TradingSessionModel).filter(
                    TradingSessionModel.session_id == session_id
                ).delete()

                return result > 0

            except Exception as e:
                logger.error(f"Failed to delete session {session_id}: {e}")
                return False

    def save_order(self, order_dict: dict, db: Optional[Session] = None) -> None:
        """
        Save order to database.

        Args:
            order_dict: Order data dictionary
            db: Optional database session
        """
        with self.managed_session(db) as db_session:
            try:
                client_order_id = str(order_dict['order_id'])
                session_order_pk = build_session_order_pk(
                    order_dict['session_id'],
                    client_order_id,
                )
                metadata_json = dict(order_dict.get('metadata') or {})
                metadata_json['client_order_id'] = client_order_id

                order = OrderModel(
                    order_id=session_order_pk,
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
                    pnl=order_dict.get('pnl'),
                    metadata_json=metadata_json,
                )

                db_session.add(order)

                logger.debug(f"Saved order {session_order_pk} to database")

            except Exception as e:
                logger.error(f"Failed to save order: {e}")
                raise

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
        with self.managed_session(db, commit_on_success=False) as db_session:
            orders = db_session.query(OrderModel).filter(
                OrderModel.session_id == session_id
            ).order_by(OrderModel.created_at).all()

            return [
                {
                    'order_id': extract_client_order_id(o),
                    'db_order_id': o.order_id,
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

    def get_session_count(self, db: Optional[Session] = None) -> dict:
        """
        Get count of sessions by status.

        Args:
            db: Optional database session

        Returns:
            dict: {status: count}
        """
        with self.managed_session(db, commit_on_success=False) as db_session:
            counts = {}

            for status in SessionStatusEnum:
                count = db_session.query(TradingSessionModel).filter(
                    TradingSessionModel.status == status
                ).count()
                counts[status.value] = count

            counts['total'] = db_session.query(TradingSessionModel).count()

            return counts
