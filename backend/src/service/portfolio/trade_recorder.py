"""
Trade Recorder Service - Centralized trade recording for portfolio operations.

This module provides a unified interface for recording trades across:
- Initial position establishment
- Rebalancing operations
- Strategy-driven trades (from Backtrader orders)

By centralizing trade recording, we ensure:
- Consistent data format across all trade sources
- Single source of truth for trade history
- Easy testing and validation
"""

from dataclasses import dataclass, asdict, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class TradeTrigger(Enum):
    """
    Enum representing the trigger/source of a trade.

    Values:
        INITIAL_POSITION: Trade from establishing initial portfolio positions
        REBALANCE: Trade from portfolio rebalancing
        STRATEGY: Trade from user strategy signals
    """
    INITIAL_POSITION = "initial_position"
    REBALANCE = "rebalance"
    STRATEGY = "strategy"


@dataclass
class TradeRecord:
    """
    Immutable record of a single trade.

    Attributes:
        date: Trade date in ISO format (YYYY-MM-DD)
        ticker: Asset symbol (e.g., "AAPL")
        action: Trade direction ("buy" or "sell")
        shares: Number of shares traded (always positive)
        price: Execution price per share
        value: Total trade value (shares * price)
        trigger: Source of the trade (TradeTrigger value)
        commission: Commission paid for this trade (default: 0.0)
    """
    date: str
    ticker: str
    action: str  # "buy" or "sell" (lowercase for consistency)
    shares: int
    price: float
    value: float
    trigger: str
    commission: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def __post_init__(self):
        """Validate and normalize trade record."""
        # Normalize action to lowercase
        self.action = self.action.lower()
        if self.action not in ("buy", "sell"):
            raise ValueError(f"Invalid action: {self.action}. Must be 'buy' or 'sell'.")

        # Ensure shares is positive
        self.shares = abs(int(self.shares))

        # Ensure price and value are positive floats
        self.price = abs(float(self.price))
        self.value = abs(float(self.value))
        self.commission = abs(float(self.commission))


class TradeRecorder:
    """
    Centralized trade recorder for portfolio operations.

    This class provides a unified interface for recording trades from
    various sources (initial positions, rebalancing, strategy signals)
    with consistent formatting and validation.

    Usage:
        recorder = TradeRecorder()

        # Record a buy trade
        recorder.record_buy(
            trade_date=date(2024, 1, 15),
            ticker="AAPL",
            shares=100,
            price=150.0,
            trigger=TradeTrigger.INITIAL_POSITION
        )

        # Get all trades
        trades = recorder.get_all_trades()

        # Get trades by trigger type
        rebalance_trades = recorder.get_trades_by_trigger(TradeTrigger.REBALANCE)
    """

    def __init__(self):
        """Initialize an empty trade recorder."""
        self._trades: List[TradeRecord] = []

    def record_trade(
        self,
        trade_date: Union[date, datetime, str],
        ticker: str,
        action: str,
        shares: int,
        price: float,
        trigger: TradeTrigger,
        commission: float = 0.0,
        value: Optional[float] = None,
    ) -> TradeRecord:
        """
        Record a trade and return the trade record.

        Args:
            trade_date: Date of the trade (date, datetime, or ISO string)
            ticker: Asset symbol
            action: "buy" or "sell"
            shares: Number of shares (will be converted to positive)
            price: Price per share
            trigger: Source of the trade (TradeTrigger enum)
            commission: Commission paid (default: 0.0)
            value: Optional explicit trade value; if None, calculated as shares * price

        Returns:
            The created TradeRecord

        Raises:
            ValueError: If action is not 'buy' or 'sell'
        """
        # Normalize date to ISO string
        if isinstance(trade_date, datetime):
            date_str = trade_date.date().isoformat()
        elif isinstance(trade_date, date):
            date_str = trade_date.isoformat()
        else:
            date_str = str(trade_date)

        # Calculate value if not provided
        if value is None:
            value = abs(shares) * price

        record = TradeRecord(
            date=date_str,
            ticker=ticker,
            action=action,
            shares=abs(shares),
            price=price,
            value=value,
            trigger=trigger.value if isinstance(trigger, TradeTrigger) else str(trigger),
            commission=commission,
        )

        self._trades.append(record)

        logger.debug(
            f"Trade recorded: {ticker} {record.action} "
            f"{record.shares} shares @ ${record.price:.2f} "
            f"(trigger: {record.trigger})"
        )

        return record

    def record_buy(
        self,
        trade_date: Union[date, datetime, str],
        ticker: str,
        shares: int,
        price: float,
        trigger: TradeTrigger,
        commission: float = 0.0,
        value: Optional[float] = None,
    ) -> TradeRecord:
        """
        Record a buy trade.

        Convenience method for recording buy trades.

        Args:
            trade_date: Date of the trade
            ticker: Asset symbol
            shares: Number of shares to buy
            price: Price per share
            trigger: Source of the trade
            commission: Commission paid (default: 0.0)
            value: Optional explicit trade value

        Returns:
            The created TradeRecord
        """
        return self.record_trade(
            trade_date=trade_date,
            ticker=ticker,
            action="buy",
            shares=shares,
            price=price,
            trigger=trigger,
            commission=commission,
            value=value,
        )

    def record_sell(
        self,
        trade_date: Union[date, datetime, str],
        ticker: str,
        shares: int,
        price: float,
        trigger: TradeTrigger,
        commission: float = 0.0,
        value: Optional[float] = None,
    ) -> TradeRecord:
        """
        Record a sell trade.

        Convenience method for recording sell trades.

        Args:
            trade_date: Date of the trade
            ticker: Asset symbol
            shares: Number of shares to sell
            price: Price per share
            trigger: Source of the trade
            commission: Commission paid (default: 0.0)
            value: Optional explicit trade value

        Returns:
            The created TradeRecord
        """
        return self.record_trade(
            trade_date=trade_date,
            ticker=ticker,
            action="sell",
            shares=shares,
            price=price,
            trigger=trigger,
            commission=commission,
            value=value,
        )

    def record_from_order(
        self,
        order,
        ticker: str,
        trade_date: Union[date, datetime, str],
        trigger: TradeTrigger = TradeTrigger.STRATEGY,
    ) -> TradeRecord:
        """
        Record a trade from a Backtrader order object.

        This method extracts trade information from a completed Backtrader
        order and records it with consistent formatting.

        Args:
            order: Backtrader order object (must be completed)
            ticker: Asset symbol (extracted from order.data if available)
            trade_date: Date of the trade
            trigger: Source of the trade (default: STRATEGY)

        Returns:
            The created TradeRecord

        Note:
            Only call this for completed orders (order.status == order.Completed)
        """
        action = "buy" if order.isbuy() else "sell"
        shares = int(abs(order.executed.size))
        price = float(order.executed.price)
        value = float(abs(order.executed.value))
        commission = float(order.executed.comm) if hasattr(order.executed, 'comm') else 0.0

        return self.record_trade(
            trade_date=trade_date,
            ticker=ticker,
            action=action,
            shares=shares,
            price=price,
            trigger=trigger,
            commission=commission,
            value=value,
        )

    def get_all_trades(self) -> List[dict]:
        """
        Get all recorded trades as a list of dictionaries.

        Returns:
            List of trade dictionaries, ordered by recording time
        """
        return [t.to_dict() for t in self._trades]

    def get_trades_by_trigger(self, trigger: TradeTrigger) -> List[dict]:
        """
        Get trades filtered by trigger type.

        Args:
            trigger: TradeTrigger to filter by

        Returns:
            List of trade dictionaries matching the trigger
        """
        trigger_value = trigger.value if isinstance(trigger, TradeTrigger) else str(trigger)
        return [t.to_dict() for t in self._trades if t.trigger == trigger_value]

    def get_trades_by_ticker(self, ticker: str) -> List[dict]:
        """
        Get trades filtered by ticker symbol.

        Args:
            ticker: Asset symbol to filter by

        Returns:
            List of trade dictionaries for the specified ticker
        """
        return [t.to_dict() for t in self._trades if t.ticker == ticker]

    def get_trades_by_action(self, action: str) -> List[dict]:
        """
        Get trades filtered by action (buy/sell).

        Args:
            action: "buy" or "sell"

        Returns:
            List of trade dictionaries matching the action
        """
        action = action.lower()
        return [t.to_dict() for t in self._trades if t.action == action]

    def get_statistics(self) -> dict:
        """
        Calculate trading statistics.

        Returns:
            Dictionary containing:
            - total_trades: Total number of trades
            - buy_trades: Number of buy trades
            - sell_trades: Number of sell trades
            - total_volume: Sum of all trade values
            - total_commission: Sum of all commissions
            - trades_by_trigger: Count of trades per trigger type
        """
        buy_trades = [t for t in self._trades if t.action == "buy"]
        sell_trades = [t for t in self._trades if t.action == "sell"]

        # Count by trigger
        trigger_counts = {}
        for t in self._trades:
            trigger_counts[t.trigger] = trigger_counts.get(t.trigger, 0) + 1

        return {
            "total_trades": len(self._trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "total_volume": sum(t.value for t in self._trades),
            "total_commission": sum(t.commission for t in self._trades),
            "trades_by_trigger": trigger_counts,
        }

    def clear(self):
        """Clear all recorded trades."""
        self._trades.clear()
        logger.debug("Trade recorder cleared")

    @property
    def trade_count(self) -> int:
        """Get the total number of recorded trades."""
        return len(self._trades)

    def __len__(self) -> int:
        """Return the number of trades recorded."""
        return len(self._trades)

    def __repr__(self) -> str:
        """Return string representation of the recorder."""
        return f"TradeRecorder(trades={len(self._trades)})"
