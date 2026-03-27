"""
Manual regression test for portfolio backtest fixes.
"""

import logging
import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_portfolio_backtest():
    """Test multi-asset backtest with sma_cross strategy."""
    from src.service.multi_asset_backtest import run_multi_asset_backtest

    logger.info("=" * 60)
    logger.info("Testing Portfolio Backtest Fix")
    logger.info("=" * 60)

    tickers = ["AAPL", "GOOGL"]
    weights = [0.5, 0.5]
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    strategy_name = "sma_cross"

    result = run_multi_asset_backtest(
        tickers=tickers,
        weights=weights,
        start_date=start_date,
        end_date=end_date,
        initial_cash=100000.0,
        commission=0.001,
        strategy_name=strategy_name,
        params={
            "fast_period": 10,
            "slow_period": 30,
        },
        timeframe="1d",
        save_path=None,
    )

    trades = result.get("all_trades", [])
    individual_results = result.get("individual_results", [])

    logger.info("Total trades: %s", len(trades))
    logger.info("Individual asset results: %s", len(individual_results))
    logger.info("Final Value: $%.2f", result.get("final_value", 0))
    logger.info("Total Return: %.2f%%", result.get("total_return", 0))

    assert result is not None
    assert "final_value" in result


if __name__ == "__main__":
    try:
        test_portfolio_backtest()
    except Exception:
        sys.exit(1)
    sys.exit(0)
