import os
import re
import importlib.util
import logging
import backtrader as bt
import yfinance as yf
import pandas as pd
import matplotlib

# Use a non-interactive backend and silence any attempts to show figures
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.ioff()
plt.show = lambda *args, **kwargs: None  # Prevent local popups in API runs

logger = logging.getLogger(__name__)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = os.path.join(BASE_DIR, "resources")
IMAGE_DIR = os.path.join(RESOURCE_DIR, "images")
STRATEGY_DIR = os.path.join(BASE_DIR, "strategy")

DEFAULT_STRATEGY_NAME = None


class StrategyLoadError(Exception):
    """Raised when the user strategy cannot be loaded."""


class DataLoadError(Exception):
    """Raised when market data cannot be loaded."""


def ensure_resource_files():
    os.makedirs(RESOURCE_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(STRATEGY_DIR, exist_ok=True)


def _sanitize_strategy_name(name: str) -> str:
    """
    Only allow simple names to avoid path traversal.
    Accepts optional '.py' suffix and always returns '<name>.py'.
    """
    if not name:
        raise StrategyLoadError("Strategy name is required")
    clean = name.strip()
    if clean.lower().endswith(".py"):
        clean = clean[:-3]
    if not re.match(r"^[A-Za-z0-9_-]+$", clean):
        raise StrategyLoadError("Strategy name must use letters, numbers, '-' or '_'")
    return f"{clean}.py"


def get_strategy_path(name: str) -> str:
    filename = _sanitize_strategy_name(name)
    return os.path.join(STRATEGY_DIR, filename)


def list_strategies():
    ensure_resource_files()
    entries = []
    for fname in os.listdir(STRATEGY_DIR):
        if fname.endswith(".py"):
            entries.append(fname[:-3])
    return sorted(set(entries))


def get_user_strategy_code(name: str):
    ensure_resource_files()
    path = get_strategy_path(name)
    if not os.path.exists(path):
        raise StrategyLoadError(f"Strategy '{name}' not found")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def save_user_strategy_code(name: str, code: str):
    ensure_resource_files()
    path = get_strategy_path(name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)


def load_user_strategy(name: str):
    ensure_resource_files()
    path = get_strategy_path(name)
    if not os.path.exists(path):
        raise StrategyLoadError(f"Strategy '{name}' not found")
    try:
        module_name = f"user_strategy_{name}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        # Register the module so Backtrader can resolve cls.__module__
        import sys

        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except Exception as exc:
        raise StrategyLoadError(f"Failed to load strategy '{name}': {exc}") from exc

    strategy_cls = getattr(module, "UserStrategy", None)
    if strategy_cls is None or not issubclass(strategy_cls, bt.Strategy):
        raise StrategyLoadError("UserStrategy class not found or not a valid Backtrader Strategy")
    return strategy_cls


def get_data(ticker, start, end):
    """
    Download data; if unavailable (e.g., network issues or bad ticker), fall back to synthetic data.
    """
    error = None
    try:
        data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        if data is None or data.empty:
            raise DataLoadError("No data returned")
    except Exception as exc:
        error = exc
        # Generate a simple synthetic price series to keep the pipeline alive
        dates = pd.date_range(start=start, end=end, freq="B")
        if len(dates) == 0:
            dates = pd.date_range(end=pd.Timestamp.today(), periods=200, freq="B")
        prices = pd.Series(100.0, index=dates).cumsum()  # monotonic increasing baseline
        data = pd.DataFrame(
            {
                "Open": prices * 0.999,
                "High": prices * 1.001,
                "Low": prices * 0.999,
                "Close": prices,
                "Adj Close": prices,
                "Volume": 1_000_000,
            },
            index=dates,
        )
        logger.warning("Data download failed for %s (%s-%s); using synthetic data. Cause: %s", ticker, start, end, exc)

    return bt.feeds.PandasData(dataname=data)


def run_backtest(
    ticker="AAPL",
    start_date="2022-01-01",
    end_date="2023-12-31",
    initial_cash=100000.0,
    commission=0.0005,
    stake=100,
    strategy_name=None,
    save_path=None,
):
    if not strategy_name:
        available = list_strategies()
        if not available:
            raise StrategyLoadError("No strategies available; please add one in /strategy")
        strategy_name = available[0]

    strategy_cls = load_user_strategy(strategy_name)

    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy_cls)

    data = get_data(ticker, start_date, end_date)
    cerebro.adddata(data)

    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    cerebro.addsizer(bt.sizers.FixedSize, stake=stake)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="annual")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name="timedraw")

    try:
        results = cerebro.run()
    except Exception as exc:
        logger.exception("Backtest run failed: %s", exc)
        raise
    strat = results[0]

    metrics = {
        "final_value": cerebro.broker.getvalue(),
        "sharpe": strat.analyzers.sharpe.get_analysis().get("sharperatio", None),
        "drawdown": strat.analyzers.drawdown.get_analysis().get("max", {}).get("drawdown", 0.0),
        "returns": strat.analyzers.returns.get_analysis().get("rnorm100", 0.0),
        "annual_returns": strat.analyzers.annual.get_analysis(),
        "sqn": strat.analyzers.sqn.get_analysis().get("sqn", None),
        "trades": strat.analyzers.trades.get_analysis(),
        "time_drawdown": strat.analyzers.timedraw.get_analysis(),
    }

    if save_path:
        try:
            plt.ioff()
            figures = cerebro.plot(style="candlestick", iplot=False)
            first_fig = figures[0][0] if figures and figures[0] else None
            if first_fig:
                first_fig.set_size_inches(18, 10)  # enlarge output
                first_fig.savefig(save_path, bbox_inches="tight", dpi=150)
                plt.close(first_fig)
            plt.close("all")
        except Exception as exc:
            logger.exception("Plot rendering failed: %s", exc)
            plt.close("all")
            raise RuntimeError(f"Failed to render plot: {exc}") from exc

    return metrics


__all__ = [
    "run_backtest",
    "get_user_strategy_code",
    "save_user_strategy_code",
    "list_strategies",
    "ensure_resource_files",
    "StrategyLoadError",
    "DEFAULT_STRATEGY_NAME",
    "STRATEGY_DIR",
    "get_strategy_path",
    "IMAGE_DIR",
]
