"""
Backtest Configuration - Immutable configuration for portfolio backtests.

This module provides:
- BacktestConfig: Validated, immutable configuration for backtests
- Validation logic extracted from run_multi_asset_backtest()
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


# Maximum number of tickers allowed (memory constraint)
MAX_TICKERS = 20

# Supported timeframes
SUPPORTED_TIMEFRAMES = [
    "1m", "5m", "15m", "30m",  # Minutes
    "1h", "4h",                 # Hours
    "1d", "1w", "1M",          # Day, Week, Month
]





@dataclass
class BacktestConfig:
    """
    Immutable configuration for portfolio backtests.

    This class encapsulates all configuration needed to run a multi-asset
    backtest, with validation to ensure all values are valid.

    Attributes:
        tickers: List of ticker symbols
        weights: Initial allocation weights (should sum to 1.0)
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
        initial_cash: Starting portfolio cash
        commission: Commission rate per trade
        strategy_name: Name of the strategy file (without .py)
        params: Strategy parameters dictionary
        timeframe: Data timeframe
    """
    tickers: List[str]
    weights: List[float]
    start_date: str
    end_date: str
    initial_cash: float = 100000.0
    commission: float = 0.0005
    strategy_name: str = ""
    params: Optional[Dict[str, Any]] = None
    timeframe: str = "1d"

    # Internal flag to track if validation has run
    _validated: bool = field(default=False, repr=False, compare=False)

    def validate(self) -> "BacktestConfig":
        """
        Validate the configuration and normalize values.

        Performs all validation checks and normalizes weights to sum to 1.0.

        Returns:
            Self, for method chaining

        Raises:
            ValueError: If any validation fails
        """
        if self._validated:
            return self

        # Validate tickers
        self._validate_tickers()

        # Validate weights
        self._validate_and_normalize_weights()

        # Validate dates
        self._validate_dates()

        # Validate numeric values
        self._validate_numeric_values()

        # Validate strategy
        self._validate_strategy()

        # Validate timeframe
        self._validate_timeframe()

        object.__setattr__(self, "_validated", True)
        return self

    def _validate_tickers(self):
        """Validate ticker list."""
        if not self.tickers:
            raise ValueError("Must provide at least one ticker")

        if len(self.tickers) > MAX_TICKERS:
            raise ValueError(
                f"Maximum {MAX_TICKERS} tickers allowed (memory limit). "
                f"Got {len(self.tickers)}."
            )

        # Check for duplicates
        if len(set(self.tickers)) != len(self.tickers):
            raise ValueError("Duplicate tickers are not allowed")

        # Check for empty strings
        if any(not t or not t.strip() for t in self.tickers):
            raise ValueError("Empty ticker symbols are not allowed")

    def _validate_and_normalize_weights(self):
        """Validate and normalize weights to sum to 1.0."""
        if len(self.weights) != len(self.tickers):
            raise ValueError(
                f"Weights length ({len(self.weights)}) must match "
                f"tickers length ({len(self.tickers)})"
            )

        if any(w < 0 for w in self.weights):
            raise ValueError("All weights must be non-negative")

        weight_sum = sum(self.weights)

        if weight_sum == 0:
            raise ValueError("Weights cannot all be zero")

        if not (0.99 <= weight_sum <= 1.01):
            logger.warning(
                f"Weights sum to {weight_sum:.3f}, normalizing to 1.0"
            )
            normalized_weights = [w / weight_sum for w in self.weights]
            object.__setattr__(self, "weights", normalized_weights)

    def _validate_dates(self):
        """Validate date format and range."""
        from datetime import datetime

        try:
            start = datetime.strptime(self.start_date, "%Y-%m-%d")
            end = datetime.strptime(self.end_date, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(
                f"Invalid date format. Use YYYY-MM-DD. Error: {e}"
            )

        if start >= end:
            raise ValueError(
                f"Start date ({self.start_date}) must be before "
                f"end date ({self.end_date})"
            )

    def _validate_numeric_values(self):
        """Validate numeric configuration values."""
        if self.initial_cash <= 0:
            raise ValueError(
                f"Initial cash must be positive. Got {self.initial_cash}"
            )

        if self.commission < 0:
            raise ValueError(
                f"Commission cannot be negative. Got {self.commission}"
            )

        if self.commission > 0.1:  # 10% seems unreasonably high
            logger.warning(
                f"Commission rate {self.commission:.2%} seems very high. "
                "Are you sure this is correct?"
            )

    def _validate_strategy(self):
        """Validate strategy name."""
        if not self.strategy_name or not self.strategy_name.strip():
            raise ValueError("Strategy name is required")

        # Check for invalid characters
        invalid_chars = set('<>:"/\\|?*')
        if any(c in self.strategy_name for c in invalid_chars):
            raise ValueError(
                f"Strategy name contains invalid characters: {invalid_chars}"
            )



    def _validate_timeframe(self):
        """Validate timeframe."""
        if self.timeframe not in SUPPORTED_TIMEFRAMES:
            logger.warning(
                f"Timeframe '{self.timeframe}' may not be supported. "
                f"Common timeframes: {SUPPORTED_TIMEFRAMES}"
            )

    @classmethod
    def from_dict(cls, data: dict) -> "BacktestConfig":
        """
        Create BacktestConfig from a dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            Validated BacktestConfig instance
        """
        return cls(
            tickers=data.get("tickers", []),
            weights=data.get("weights", []),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            initial_cash=data.get("initial_cash", 100000.0),
            commission=data.get("commission", 0.0005),
            strategy_name=data.get("strategy_name", ""),
            params=data.get("params"),
            timeframe=data.get("timeframe", "1d"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "tickers": self.tickers,
            "weights": self.weights,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_cash": self.initial_cash,
            "commission": self.commission,
            "strategy_name": self.strategy_name,
            "params": self.params,
            "timeframe": self.timeframe,
        }

    def get_ticker_weight_dict(self) -> Dict[str, float]:
        """Get ticker-to-weight mapping."""
        return dict(zip(self.tickers, self.weights))

    def __repr__(self) -> str:
        return (
            f"BacktestConfig(tickers={self.tickers}, "
            f"weights={[f'{w:.2%}' for w in self.weights]}, "
            f"dates={self.start_date}~{self.end_date}, "
            f"cash=${self.initial_cash:,.0f})"
        )


__all__ = [
    "BacktestConfig",
    "MAX_TICKERS",
    "SUPPORTED_TIMEFRAMES",
]
