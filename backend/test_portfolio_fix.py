"""
Test script to verify portfolio backtest fixes
"""

import sys
import logging
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_portfolio_backtest():
    """Test multi-asset backtest with sma_cross_multi_asset strategy"""
    from src.service.multi_asset_backtest import run_multi_asset_backtest

    logger.info("="*60)
    logger.info("Testing Portfolio Backtest Fix")
    logger.info("="*60)

    # Test configuration
    tickers = ["AAPL", "GOOGL"]
    weights = [0.5, 0.5]
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    strategy_name = "sma_cross"  # Use existing single-asset strategy (will only trade first asset)

    logger.info(f"Configuration:")
    logger.info(f"  Tickers: {tickers}")
    logger.info(f"  Weights: {weights}")
    logger.info(f"  Date range: {start_date} to {end_date}")
    logger.info(f"  Strategy: {strategy_name}")

    try:
        # Run backtest
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
                "position_size": 100,
            },
            rebalance_config=None,
            optimization_method="equal_weight",
            timeframe="1d",
            save_path=None,
        )

        logger.info("\n" + "="*60)
        logger.info("BACKTEST RESULTS")
        logger.info("="*60)

        # Check trades
        trades = result.get("all_trades", [])
        logger.info(f"\n✓ Total trades: {len(trades)}")

        if trades:
            logger.info("\nFirst 5 trades:")
            for trade in trades[:5]:
                logger.info(f"  - {trade['date']} | {trade['ticker']} | {trade['action']} | "
                           f"{trade['shares']} shares @ ${trade['price']:.2f}")
        else:
            logger.warning("⚠ NO TRADES RECORDED!")

        # Check individual results
        individual_results = result.get("individual_results", [])
        logger.info(f"\n✓ Individual asset results: {len(individual_results)}")

        for asset in individual_results:
            logger.info(f"\n  {asset['ticker']}:")
            logger.info(f"    Initial: ${asset.get('initial_cash', 0):,.2f}")
            logger.info(f"    Final: ${asset.get('final_value', 0):,.2f}")
            logger.info(f"    Return: {asset.get('total_return', 0):.2f}%")

        # Check overall performance
        logger.info(f"\n✓ Portfolio Performance:")
        logger.info(f"    Final Value: ${result.get('final_value', 0):,.2f}")
        logger.info(f"    Total Return: {result.get('total_return', 0):.2f}%")
        logger.info(f"    Sharpe Ratio: {result.get('sharpe_ratio', 0):.2f}")
        logger.info(f"    Max Drawdown: {result.get('max_drawdown', 0):.2f}%")

        logger.info("\n" + "="*60)
        logger.info("✓ TEST PASSED")
        logger.info("="*60)

        return True

    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_portfolio_backtest()
    sys.exit(0 if success else 1)
