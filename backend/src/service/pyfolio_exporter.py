"""
PyFolio Exporter Service - Export backtest data in PyFolio-compatible format.

Provides functionality to:
- Export returns as pandas Series (PyFolio format)
- Export transactions with position tracking
- Generate PyFolio tear sheet (if pyfolio is installed)
- Export data to CSV files for external PyFolio analysis
"""

import io
import logging
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PyFolioExportError(Exception):
    """Raised when PyFolio data export fails."""


def _parse_equity_curve(equity_curve: Dict[str, float]) -> pd.Series:
    """
    Parse equity curve dict to pandas Series of daily returns.

    Args:
        equity_curve: Dict mapping date strings to daily returns

    Returns:
        pd.Series with DatetimeIndex and daily returns
    """
    if not equity_curve:
        return pd.Series(dtype=float)

    returns_data = {}
    for date_str, return_val in equity_curve.items():
        try:
            date = pd.Timestamp(date_str)
            returns_data[date] = float(return_val)
        except (ValueError, TypeError):
            continue

    series = pd.Series(returns_data)
    series = series.sort_index()
    series.index.name = "date"
    series.name = "returns"

    return series


def _parse_trade_details(
    trade_details: Dict[str, Any],
    ticker: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Parse trade details to PyFolio-compatible transactions and positions.

    PyFolio expects:
    - transactions: DataFrame with columns [amount, price, symbol] indexed by datetime
    - positions: DataFrame with asset columns and 'cash' column indexed by datetime

    Args:
        trade_details: Trade details from TradeRecorder analyzer
        ticker: Trading symbol

    Returns:
        Tuple of (transactions DataFrame, positions DataFrame)
    """
    trades = trade_details.get("trades", [])

    if not trades:
        return pd.DataFrame(), pd.DataFrame()

    # Build transactions DataFrame
    transactions_list = []

    for trade in trades:
        # Entry transaction
        entry_date = trade.get("entry_date")
        entry_price = trade.get("entry_price", 0)
        size = trade.get("size", 0)

        if entry_date and entry_price:
            try:
                transactions_list.append({
                    "date": pd.Timestamp(entry_date),
                    "amount": size,  # Positive for buy
                    "price": entry_price,
                    "symbol": ticker,
                })
            except (ValueError, TypeError):
                pass

        # Exit transaction
        exit_date = trade.get("exit_date")
        exit_price = trade.get("exit_price", 0)

        if exit_date and exit_price:
            try:
                transactions_list.append({
                    "date": pd.Timestamp(exit_date),
                    "amount": -size,  # Negative for sell
                    "price": exit_price,
                    "symbol": ticker,
                })
            except (ValueError, TypeError):
                pass

    if not transactions_list:
        return pd.DataFrame(), pd.DataFrame()

    transactions_df = pd.DataFrame(transactions_list)
    transactions_df = transactions_df.set_index("date").sort_index()

    # Build positions DataFrame (simplified - track cumulative position)
    positions_list = []
    cumulative_position = 0

    for _, txn in transactions_df.iterrows():
        cumulative_position += txn["amount"]
        positions_list.append({
            "date": txn.name,
            ticker: cumulative_position * txn["price"],
            "cash": 0,  # Simplified - PyFolio can handle this
        })

    if positions_list:
        positions_df = pd.DataFrame(positions_list)
        positions_df = positions_df.set_index("date").sort_index()
    else:
        positions_df = pd.DataFrame()

    return transactions_df, positions_df


def export_pyfolio_data(
    equity_curve: Dict[str, float],
    trade_details: Dict[str, Any],
    ticker: str,
    initial_cash: float = 100000.0,
) -> Dict[str, pd.DataFrame]:
    """
    Export backtest data in PyFolio-compatible format.

    Args:
        equity_curve: Dict mapping date strings to daily returns
        trade_details: Trade details from TradeRecorder analyzer
        ticker: Trading symbol
        initial_cash: Initial portfolio value

    Returns:
        Dict with 'returns', 'transactions', 'positions' DataFrames

    Raises:
        PyFolioExportError: If export fails
    """
    if not equity_curve:
        raise PyFolioExportError("Equity curve is empty - cannot export data")

    # Parse returns
    returns = _parse_equity_curve(equity_curve)

    if returns.empty:
        raise PyFolioExportError("Failed to parse equity curve data")

    # Parse transactions and positions
    transactions, positions = _parse_trade_details(trade_details, ticker)

    return {
        "returns": returns,
        "transactions": transactions,
        "positions": positions,
    }


def export_to_csv_zip(
    equity_curve: Dict[str, float],
    trade_details: Dict[str, Any],
    ticker: str,
    backtest_id: str,
    initial_cash: float = 100000.0,
    include_quantstats: bool = True,
) -> bytes:
    """
    Export backtest data as a ZIP file containing CSV files.

    The ZIP file contains:
    - returns.csv: Daily returns series
    - transactions.csv: All transactions
    - positions.csv: Position values over time
    - metadata.json: Backtest metadata

    Args:
        equity_curve: Dict mapping date strings to daily returns
        trade_details: Trade details from TradeRecorder analyzer
        ticker: Trading symbol
        backtest_id: Unique backtest identifier
        initial_cash: Initial portfolio value
        include_quantstats: Include QuantStats-compatible format

    Returns:
        ZIP file as bytes

    Raises:
        PyFolioExportError: If export fails
    """
    import json

    data = export_pyfolio_data(equity_curve, trade_details, ticker, initial_cash)

    # Create ZIP file in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Returns CSV
        returns_csv = data["returns"].to_csv(header=True)
        zf.writestr("returns.csv", returns_csv)

        # Transactions CSV
        if not data["transactions"].empty:
            transactions_csv = data["transactions"].to_csv(index=True)
            zf.writestr("transactions.csv", transactions_csv)

        # Positions CSV
        if not data["positions"].empty:
            positions_csv = data["positions"].to_csv(index=True)
            zf.writestr("positions.csv", positions_csv)

        # Metadata JSON
        metadata = {
            "backtest_id": backtest_id,
            "ticker": ticker,
            "initial_cash": initial_cash,
            "export_date": datetime.utcnow().isoformat() + "Z",
            "data_points": len(data["returns"]),
            "transactions_count": len(data["transactions"]),
            "format": "pyfolio-compatible",
            "usage_instructions": {
                "pyfolio": (
                    "import pandas as pd\n"
                    "import pyfolio as pf\n\n"
                    "returns = pd.read_csv('returns.csv', index_col=0, parse_dates=True)['returns']\n"
                    "pf.create_full_tear_sheet(returns)"
                ),
                "quantstats": (
                    "import pandas as pd\n"
                    "import quantstats as qs\n\n"
                    "returns = pd.read_csv('returns.csv', index_col=0, parse_dates=True)['returns']\n"
                    "qs.reports.html(returns, output='report.html')"
                ),
            },
        }
        zf.writestr("metadata.json", json.dumps(metadata, indent=2))

        # README file
        readme_content = """# PyFolio Export Data

## Files
- `returns.csv` - Daily returns series (required for PyFolio)
- `transactions.csv` - Trade transactions (optional for PyFolio)
- `positions.csv` - Position values over time (optional)
- `metadata.json` - Export metadata and usage instructions

## Usage with PyFolio

```python
import pandas as pd
import pyfolio as pf

# Load returns
returns = pd.read_csv('returns.csv', index_col=0, parse_dates=True)['returns']

# Create tear sheet
pf.create_full_tear_sheet(returns)

# Or with transactions
transactions = pd.read_csv('transactions.csv', index_col=0, parse_dates=True)
pf.create_full_tear_sheet(returns, transactions=transactions)
```

## Usage with QuantStats

```python
import pandas as pd
import quantstats as qs

returns = pd.read_csv('returns.csv', index_col=0, parse_dates=True)['returns']

# Generate HTML report
qs.reports.html(returns, output='report.html')

# Or display in notebook
qs.reports.full(returns)
```
"""
        zf.writestr("README.md", readme_content)

    zip_buffer.seek(0)
    return zip_buffer.read()


def generate_tear_sheet_html(
    equity_curve: Dict[str, float],
    trade_details: Dict[str, Any],
    ticker: str,
    strategy_name: str = "Strategy",
    initial_cash: float = 100000.0,
    benchmark_ticker: Optional[str] = None,
) -> Optional[str]:
    """
    Generate a tear sheet HTML report using QuantStats.

    QuantStats is preferred over PyFolio due to better maintenance
    and modern Python compatibility.

    Args:
        equity_curve: Dict mapping date strings to daily returns
        trade_details: Trade details from TradeRecorder analyzer
        ticker: Trading symbol
        strategy_name: Strategy name for report title
        initial_cash: Initial portfolio value
        benchmark_ticker: Optional benchmark ticker for comparison

    Returns:
        HTML string of tear sheet, or None if generation fails
    """
    import tempfile
    import os

    try:
        import quantstats as qs
    except ImportError:
        logger.warning("QuantStats not installed - cannot generate tear sheet")
        return None

    try:
        # Configure matplotlib for non-interactive backend BEFORE any plotting
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.ioff()  # Turn off interactive mode

        data = export_pyfolio_data(equity_curve, trade_details, ticker, initial_cash)
        returns = data["returns"]

        if returns.empty:
            return None

        # QuantStats requires a file path, not a StringIO buffer
        # Use a temporary file to generate the HTML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            # Generate HTML report to temporary file
            qs.reports.html(
                returns,
                benchmark=benchmark_ticker,
                title=f"{strategy_name} - {ticker}",
                output=tmp_path,
            )

            # Read the generated HTML
            with open(tmp_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            return html_content

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            # Close any open matplotlib figures
            plt.close('all')

    except Exception as e:
        logger.exception(f"Failed to generate tear sheet: {e}")
        return None


def get_pyfolio_metrics(
    equity_curve: Dict[str, float],
    risk_free_rate: float = 0.02,
) -> Dict[str, Any]:
    """
    Calculate PyFolio-style performance metrics.

    Args:
        equity_curve: Dict mapping date strings to daily returns
        risk_free_rate: Annual risk-free rate

    Returns:
        Dict with various performance metrics
    """
    returns = _parse_equity_curve(equity_curve)

    if returns.empty or len(returns) < 2:
        return {}

    # Calculate metrics
    returns_array = returns.values

    # Annual return
    total_return = (1 + returns_array).prod() - 1
    n_years = len(returns) / 252
    annual_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0

    # Volatility
    annual_volatility = returns.std() * np.sqrt(252)

    # Sharpe ratio
    daily_rf = risk_free_rate / 252
    excess_returns = returns - daily_rf
    sharpe = np.sqrt(252) * excess_returns.mean() / returns.std() if returns.std() > 0 else 0

    # Sortino ratio (downside deviation)
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
    sortino = (annual_return - risk_free_rate) / downside_std if downside_std > 0 else 0

    # Max drawdown
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()

    # Calmar ratio
    calmar = -annual_return / max_drawdown if max_drawdown < 0 else 0

    # VaR and CVaR (95%)
    var_95 = np.percentile(returns_array, 5)
    cvar_95 = returns_array[returns_array <= var_95].mean() if len(returns_array[returns_array <= var_95]) > 0 else var_95

    # Skewness and Kurtosis
    skewness = float(pd.Series(returns_array).skew())
    kurtosis = float(pd.Series(returns_array).kurtosis())

    # Win rate
    win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0

    return {
        "annual_return": round(float(annual_return), 4),
        "annual_volatility": round(float(annual_volatility), 4),
        "sharpe_ratio": round(float(sharpe), 4),
        "sortino_ratio": round(float(sortino), 4),
        "max_drawdown": round(float(max_drawdown), 4),
        "calmar_ratio": round(float(calmar), 4),
        "var_95": round(float(var_95), 6),
        "cvar_95": round(float(cvar_95), 6),
        "skewness": round(float(skewness), 4),
        "kurtosis": round(float(kurtosis), 4),
        "win_rate": round(float(win_rate), 4),
        "total_return": round(float(total_return), 4),
        "trading_days": len(returns),
    }


__all__ = [
    "export_pyfolio_data",
    "export_to_csv_zip",
    "generate_tear_sheet_html",
    "get_pyfolio_metrics",
    "PyFolioExportError",
]
