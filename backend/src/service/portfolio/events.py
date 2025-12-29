"""
Portfolio Events - Event definitions and event bus for loose coupling.

This module provides an event-based communication pattern for portfolio
components, enabling loose coupling between Strategy and Analyzers.

Key benefits:
- Strategy doesn't need to know about Analyzer internals
- Analyzers subscribe to events they care about
- Easy to add new event types without modifying existing code
- Improved testability (can test event emission independently)

Usage in Strategy:
    self.event_bus = PortfolioEventBus()
    self.event_bus.emit(RebalanceExecutedEvent(...))

Usage in Analyzer:
    def start(self):
        if hasattr(self.strategy, 'event_bus'):
            self.strategy.event_bus.subscribe(
                PortfolioEventType.REBALANCE_EXECUTED,
                self._on_rebalance
            )
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Callable, Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class PortfolioEventType(Enum):
    """
    Types of events emitted during portfolio operations.

    Events are categorized by their source and purpose:
    - Position events: Initial positions, position changes
    - Rebalance events: Rebalancing operations
    - Trade events: Individual trade executions
    - Value events: Portfolio value updates
    """
    # Position lifecycle events
    INITIAL_POSITIONS_ESTABLISHED = "initial_positions_established"
    POSITION_CHANGED = "position_changed"

    # Rebalancing events
    REBALANCE_TRIGGERED = "rebalance_triggered"
    REBALANCE_EXECUTED = "rebalance_executed"
    REBALANCE_SKIPPED = "rebalance_skipped"

    # Trade events
    TRADE_EXECUTED = "trade_executed"
    ORDER_PLACED = "order_placed"
    ORDER_COMPLETED = "order_completed"

    # Portfolio value events
    PORTFOLIO_VALUE_UPDATED = "portfolio_value_updated"


@dataclass
class PortfolioEvent:
    """
    Base class for all portfolio events.

    Attributes:
        event_type: Type of the event (from PortfolioEventType)
        timestamp: When the event occurred
        data: Additional event-specific data
    """
    event_type: PortfolioEventType
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }


@dataclass
class RebalanceExecutedEvent(PortfolioEvent):
    """
    Event emitted after a rebalancing operation completes.

    Contains all information about the rebalancing:
    - Pre/post values and weights
    - Orders executed
    - Transaction costs
    """
    event_type: PortfolioEventType = field(
        default=PortfolioEventType.REBALANCE_EXECUTED,
        init=False
    )
    date: Union[datetime, date] = field(default=None)
    trigger: str = ""
    pre_value: float = 0.0
    post_value: float = 0.0
    target_weights: Dict[str, float] = field(default_factory=dict)
    pre_weights: Dict[str, float] = field(default_factory=dict)
    orders: Dict[str, int] = field(default_factory=dict)
    transaction_cost: float = 0.0
    prices: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now()
        if self.timestamp is None:
            self.timestamp = (
                self.date if isinstance(self.date, datetime)
                else datetime.combine(self.date, datetime.min.time())
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "event_type": self.event_type.value,
            "date": (
                self.date.isoformat() if isinstance(self.date, (datetime, date))
                else str(self.date)
            ),
            "trigger": self.trigger,
            "pre_value": self.pre_value,
            "post_value": self.post_value,
            "target_weights": self.target_weights,
            "pre_weights": self.pre_weights,
            "orders": self.orders,
            "transaction_cost": self.transaction_cost,
            "prices": self.prices,
        }


@dataclass
class InitialPositionsEvent(PortfolioEvent):
    """
    Event emitted after initial positions are established.
    """
    event_type: PortfolioEventType = field(
        default=PortfolioEventType.INITIAL_POSITIONS_ESTABLISHED,
        init=False
    )
    date: Union[datetime, date] = field(default=None)
    positions: Dict[str, int] = field(default_factory=dict)
    weights: Dict[str, float] = field(default_factory=dict)
    prices: Dict[str, float] = field(default_factory=dict)
    total_value: float = 0.0

    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now()
        if self.timestamp is None:
            self.timestamp = (
                self.date if isinstance(self.date, datetime)
                else datetime.combine(self.date, datetime.min.time())
            )


@dataclass
class TradeExecutedEvent(PortfolioEvent):
    """
    Event emitted when a trade is executed.
    """
    event_type: PortfolioEventType = field(
        default=PortfolioEventType.TRADE_EXECUTED,
        init=False
    )
    date: Union[datetime, date] = field(default=None)
    ticker: str = ""
    action: str = ""  # "buy" or "sell"
    shares: int = 0
    price: float = 0.0
    value: float = 0.0
    trigger: str = ""
    commission: float = 0.0

    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now()
        if self.timestamp is None:
            self.timestamp = (
                self.date if isinstance(self.date, datetime)
                else datetime.combine(self.date, datetime.min.time())
            )


@dataclass
class PortfolioValueEvent(PortfolioEvent):
    """
    Event emitted when portfolio value is updated.
    """
    event_type: PortfolioEventType = field(
        default=PortfolioEventType.PORTFOLIO_VALUE_UPDATED,
        init=False
    )
    date: Union[datetime, date] = field(default=None)
    value: float = 0.0
    cash: float = 0.0
    positions_value: float = 0.0

    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now()
        if self.timestamp is None:
            self.timestamp = (
                self.date if isinstance(self.date, datetime)
                else datetime.combine(self.date, datetime.min.time())
            )


# Type alias for event handlers
EventHandler = Callable[[PortfolioEvent], None]


class PortfolioEventBus:
    """
    Simple event bus for portfolio events.

    Implements a publish-subscribe pattern for loose coupling between
    portfolio components (Strategy, Analyzers, etc.).

    Thread safety: This implementation is NOT thread-safe. All operations
    should occur on the same thread (Backtrader's main thread).

    Usage:
        # In Strategy.__init__
        self.event_bus = PortfolioEventBus()

        # In Analyzer.start
        self.strategy.event_bus.subscribe(
            PortfolioEventType.REBALANCE_EXECUTED,
            self._on_rebalance
        )

        # In Strategy._execute_rebalance
        self.event_bus.emit(RebalanceExecutedEvent(...))
    """

    def __init__(self):
        """Initialize the event bus."""
        self._subscribers: Dict[PortfolioEventType, List[EventHandler]] = {}
        self._event_history: List[PortfolioEvent] = []
        self._max_history: int = 1000  # Prevent unbounded growth

    def subscribe(
        self,
        event_type: PortfolioEventType,
        handler: EventHandler
    ) -> None:
        """
        Subscribe a handler to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Callable that will be invoked when event is emitted

        Note:
            The same handler can be subscribed multiple times.
            Each subscription will result in a separate invocation.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(handler)

        logger.debug(
            f"Handler subscribed to {event_type.value}: "
            f"{handler.__name__ if hasattr(handler, '__name__') else str(handler)}"
        )

    def unsubscribe(
        self,
        event_type: PortfolioEventType,
        handler: EventHandler
    ) -> bool:
        """
        Unsubscribe a handler from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to remove

        Returns:
            True if handler was found and removed, False otherwise
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                logger.debug(f"Handler unsubscribed from {event_type.value}")
                return True
            except ValueError:
                pass
        return False

    def emit(self, event: PortfolioEvent) -> None:
        """
        Emit an event to all subscribed handlers.

        Args:
            event: Event to emit

        Note:
            Handlers are invoked synchronously in subscription order.
            If a handler raises an exception, it is logged but other
            handlers will still be invoked.
        """
        # Store in history (with size limit)
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

        # Get handlers for this event type
        handlers = self._subscribers.get(event.event_type, [])

        if not handlers:
            logger.debug(f"No handlers for event: {event.event_type.value}")
            return

        logger.debug(
            f"Emitting {event.event_type.value} to {len(handlers)} handlers"
        )

        # Invoke handlers
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                handler_name = (
                    handler.__name__ if hasattr(handler, '__name__')
                    else str(handler)
                )
                logger.warning(
                    f"Event handler {handler_name} failed for "
                    f"{event.event_type.value}: {e}"
                )

    def emit_rebalance(
        self,
        date: Union[datetime, date],
        trigger: str,
        pre_value: float,
        post_value: float,
        target_weights: Dict[str, float],
        pre_weights: Dict[str, float],
        orders: Dict[str, int],
        transaction_cost: float,
        prices: Dict[str, float],
    ) -> None:
        """
        Convenience method to emit a rebalance event.

        Creates and emits a RebalanceExecutedEvent with the provided data.
        """
        event = RebalanceExecutedEvent(
            timestamp=datetime.now(),
            date=date,
            trigger=trigger,
            pre_value=pre_value,
            post_value=post_value,
            target_weights=target_weights,
            pre_weights=pre_weights,
            orders=orders,
            transaction_cost=transaction_cost,
            prices=prices,
        )
        self.emit(event)

    def emit_trade(
        self,
        date: Union[datetime, date],
        ticker: str,
        action: str,
        shares: int,
        price: float,
        trigger: str,
        commission: float = 0.0,
    ) -> None:
        """
        Convenience method to emit a trade event.
        """
        event = TradeExecutedEvent(
            timestamp=datetime.now(),
            date=date,
            ticker=ticker,
            action=action,
            shares=shares,
            price=price,
            value=shares * price,
            trigger=trigger,
            commission=commission,
        )
        self.emit(event)

    def get_event_history(
        self,
        event_type: Optional[PortfolioEventType] = None
    ) -> List[PortfolioEvent]:
        """
        Get event history, optionally filtered by type.

        Args:
            event_type: Optional type to filter by

        Returns:
            List of events (copies to prevent modification)
        """
        if event_type is None:
            return list(self._event_history)

        return [e for e in self._event_history if e.event_type == event_type]

    def clear_history(self) -> None:
        """Clear the event history."""
        self._event_history.clear()

    def get_subscriber_count(
        self,
        event_type: Optional[PortfolioEventType] = None
    ) -> int:
        """
        Get the number of subscribers.

        Args:
            event_type: Specific event type, or None for total count

        Returns:
            Number of subscribed handlers
        """
        if event_type is None:
            return sum(len(handlers) for handlers in self._subscribers.values())

        return len(self._subscribers.get(event_type, []))

    def __repr__(self) -> str:
        total_handlers = self.get_subscriber_count()
        return f"PortfolioEventBus(handlers={total_handlers})"


__all__ = [
    # Event types
    "PortfolioEventType",
    # Event classes
    "PortfolioEvent",
    "RebalanceExecutedEvent",
    "InitialPositionsEvent",
    "TradeExecutedEvent",
    "PortfolioValueEvent",
    # Event bus
    "PortfolioEventBus",
    "EventHandler",
]
