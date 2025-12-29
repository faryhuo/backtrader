"""
Rebalance Date Generator - Unified date generation for portfolio rebalancing.

This module provides a polymorphic approach to generating rebalancing dates
for different frequencies (monthly, quarterly, annually).

The design uses the Strategy pattern to encapsulate date generation logic,
making it easy to add new frequencies without modifying existing code.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class DateGeneratorStrategy(ABC):
    """
    Abstract base class for date generation strategies.

    Subclasses implement specific date generation logic for different frequencies.
    """

    @abstractmethod
    def generate(
        self,
        start_date: datetime,
        end_date: datetime,
        position: str = "first",  # "first" or "last"
        custom_day: Optional[int] = None
    ) -> List[datetime]:
        """
        Generate rebalancing dates within the specified range.

        Args:
            start_date: Start of the date range
            end_date: End of the date range
            position: "first" for start of period, "last" for end of period
            custom_day: Optional custom day of month

        Returns:
            List of datetime objects representing rebalancing dates
        """
        pass


class MonthlyDateGenerator(DateGeneratorStrategy):
    """Generate monthly rebalancing dates."""

    def generate(
        self,
        start_date: datetime,
        end_date: datetime,
        position: str = "first",
        custom_day: Optional[int] = None
    ) -> List[datetime]:
        dates = []
        current = datetime(start_date.year, start_date.month, 1)

        while current <= end_date:
            target = self._get_target_date(current, position, custom_day)

            if start_date <= target <= end_date:
                dates.append(target)

            # Move to next month
            current = self._next_month(current)

        return dates

    def _get_target_date(
        self,
        current: datetime,
        position: str,
        custom_day: Optional[int]
    ) -> datetime:
        """Calculate target date for a specific month."""
        if custom_day:
            return self._get_custom_day(current, custom_day)
        elif position == "last":
            return self._get_last_day_of_month(current)
        else:
            return datetime(current.year, current.month, 1)

    def _get_custom_day(self, current: datetime, day: int) -> datetime:
        """Get custom day, handling month boundary cases."""
        try:
            return datetime(current.year, current.month, day)
        except ValueError:
            # Day doesn't exist in this month (e.g., Feb 30)
            return self._get_last_day_of_month(current)

    def _get_last_day_of_month(self, current: datetime) -> datetime:
        """Get the last day of the month."""
        if current.month == 12:
            return datetime(current.year, 12, 31)
        else:
            return datetime(current.year, current.month + 1, 1) - timedelta(days=1)

    def _next_month(self, current: datetime) -> datetime:
        """Advance to the first day of next month."""
        if current.month == 12:
            return datetime(current.year + 1, 1, 1)
        else:
            return datetime(current.year, current.month + 1, 1)


class QuarterlyDateGenerator(DateGeneratorStrategy):
    """Generate quarterly rebalancing dates."""

    # Quarter start months
    QUARTER_MONTHS = [1, 4, 7, 10]

    # Last days of each quarter (Mar, Jun, Sep, Dec)
    QUARTER_END_DATES = {
        1: (3, 31),   # Q1 ends March 31
        4: (6, 30),   # Q2 ends June 30
        7: (9, 30),   # Q3 ends September 30
        10: (12, 31)  # Q4 ends December 31
    }

    def generate(
        self,
        start_date: datetime,
        end_date: datetime,
        position: str = "first",
        custom_day: Optional[int] = None
    ) -> List[datetime]:
        dates = []

        for year in range(start_date.year, end_date.year + 1):
            for month in self.QUARTER_MONTHS:
                target = self._get_target_date(year, month, position)

                if start_date <= target <= end_date:
                    dates.append(target)

        return sorted(dates)

    def _get_target_date(self, year: int, month: int, position: str) -> datetime:
        """Calculate target date for a specific quarter."""
        if position == "last":
            end_month, end_day = self.QUARTER_END_DATES[month]
            return datetime(year, end_month, end_day)
        else:
            return datetime(year, month, 1)


class AnnuallyDateGenerator(DateGeneratorStrategy):
    """Generate annual rebalancing dates."""

    def generate(
        self,
        start_date: datetime,
        end_date: datetime,
        position: str = "first",
        custom_day: Optional[int] = None
    ) -> List[datetime]:
        dates = []

        for year in range(start_date.year, end_date.year + 1):
            if position == "last":
                target = datetime(year, 12, 31)
            else:
                target = datetime(year, 1, 1)

            if start_date <= target <= end_date:
                dates.append(target)

        return dates


class RebalanceDateGenerator:
    """
    Factory for generating rebalancing dates.

    Provides a unified interface for generating dates across different frequencies.
    Uses the Strategy pattern internally to delegate to specialized generators.

    Usage:
        generator = RebalanceDateGenerator()
        dates = generator.generate(
            frequency="monthly_last",
            start_date=start,
            end_date=end,
            custom_day=15
        )
    """

    # Map frequency prefixes to generator classes
    _generators = {
        "monthly": MonthlyDateGenerator,
        "quarterly": QuarterlyDateGenerator,
        "annually": AnnuallyDateGenerator,
    }

    @classmethod
    def generate(
        cls,
        frequency: str,
        start_date: datetime,
        end_date: datetime,
        custom_day: Optional[int] = None
    ) -> List[datetime]:
        """
        Generate rebalancing dates for the given frequency and date range.

        Args:
            frequency: Rebalancing frequency (e.g., "monthly", "quarterly_last")
            start_date: Start of the date range
            end_date: End of the date range
            custom_day: Optional custom day of month (for monthly frequency)

        Returns:
            List of datetime objects representing rebalancing dates

        Raises:
            ValueError: If frequency is not supported
        """
        # Parse frequency to determine generator and position
        generator_key, position = cls._parse_frequency(frequency)

        # Get the appropriate generator
        generator_class = cls._generators.get(generator_key)
        if generator_class is None:
            supported = list(cls._generators.keys())
            raise ValueError(
                f"Unsupported frequency prefix: {generator_key}. "
                f"Supported: {supported}"
            )

        generator = generator_class()

        dates = generator.generate(
            start_date=start_date,
            end_date=end_date,
            position=position,
            custom_day=custom_day
        )

        logger.debug(
            f"Generated {len(dates)} {frequency} rebalancing dates "
            f"from {start_date.date()} to {end_date.date()}"
        )

        return dates

    @classmethod
    def _parse_frequency(cls, frequency: str) -> tuple:
        """
        Parse frequency string into generator key and position.

        Args:
            frequency: Frequency string (e.g., "monthly_last", "quarterly")

        Returns:
            Tuple of (generator_key, position)
        """
        frequency = frequency.lower()

        # Check for position suffix
        if "_last" in frequency:
            position = "last"
            generator_key = frequency.replace("_last", "")
        elif "_first" in frequency:
            position = "first"
            generator_key = frequency.replace("_first", "")
        else:
            position = "first"  # Default
            generator_key = frequency

        return generator_key, position

    @classmethod
    def get_supported_frequencies(cls) -> List[str]:
        """
        Get list of all supported frequency strings.

        Returns:
            List of supported frequency strings
        """
        frequencies = []
        for key in cls._generators.keys():
            frequencies.extend([
                key,
                f"{key}_first",
                f"{key}_last",
            ])
        return frequencies


def is_rebalance_date(
    current_date: datetime,
    rebalance_dates: List[datetime]
) -> bool:
    """
    Check if the current date is a rebalancing date.

    Uses O(1) set lookup instead of O(n) linear search.

    Args:
        current_date: Date to check
        rebalance_dates: List of rebalancing dates

    Returns:
        True if current_date is a rebalancing date
    """
    # Normalize to date objects for comparison
    current_date_only = (
        current_date.date() if isinstance(current_date, datetime)
        else current_date
    )

    # Build set for O(1) lookup
    rebalance_date_set = {
        d.date() if isinstance(d, datetime) else d
        for d in rebalance_dates
    }

    return current_date_only in rebalance_date_set


__all__ = [
    "DateGeneratorStrategy",
    "MonthlyDateGenerator",
    "QuarterlyDateGenerator",
    "AnnuallyDateGenerator",
    "RebalanceDateGenerator",
    "is_rebalance_date",
]
