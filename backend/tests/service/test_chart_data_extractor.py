import backtrader as bt
import pandas as pd

from src.service.chart_data_extractor import build_backtest_chart_data


class TestBuildBacktestChartData:
    def test_extracts_price_indicator_trade_and_equity_data(self):
        class SampleStrategy(bt.Strategy):
            def __init__(self):
                self.sma = bt.indicators.SMA(self.data.close, period=3)
                self.macd = bt.indicators.MACD(
                    self.data.close,
                    period_me1=3,
                    period_me2=6,
                    period_signal=3,
                )

            def next(self):
                return None

        dates = pd.date_range("2024-01-01", periods=12, freq="D")
        values = [100 + index for index in range(12)]
        data = pd.DataFrame(
            {
                "open": values,
                "high": [value + 1 for value in values],
                "low": [value - 1 for value in values],
                "close": values,
                "volume": [1000] * 12,
            },
            index=dates,
        )

        cerebro = bt.Cerebro()
        cerebro.addstrategy(SampleStrategy)
        cerebro.adddata(bt.feeds.PandasData(dataname=data))
        strat = cerebro.run()[0]

        price_data = [
            {
                "time": date.strftime("%Y-%m-%d"),
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
            }
            for date, row in data.iterrows()
        ]
        metrics = {
            "equity_curve": {
                "2024-01-01": 0.01,
                "2024-01-02": -0.02,
                "2024-01-03": 0.03,
            },
            "trade_details": {
                "trades": [
                    {
                        "trade_num": 1,
                        "entry_date": "2024-01-04",
                        "entry_price": 103.0,
                        "exit_date": "2024-01-08",
                        "exit_price": 107.0,
                        "size": 10,
                        "net_pnl": 40.0,
                    }
                ]
            },
        }

        chart_data = build_backtest_chart_data(
            strat,
            price_data,
            metrics,
            initial_cash=100000.0,
        )

        assert len(chart_data["ohlcv"]) == 12
        assert len(chart_data["markers"]) >= 2
        assert chart_data["markers"][0]["side"] == "buy"
        assert chart_data["markers"][1]["side"] == "sell"
        assert chart_data["markers"][1]["pnl"] == 40.0
        assert len(chart_data["equity_curve"]) == 3
        assert chart_data["equity_curve"][0]["value"] == 101000.0
        assert any(indicator["name"] == "SMA" for indicator in chart_data["indicators"])
        assert any(indicator["subplot"] for indicator in chart_data["indicators"])
        trade_observer = next(
            (indicator for indicator in chart_data["indicators"] if indicator["name"] == "Trades"),
            None,
        )
        if trade_observer is not None:
            assert trade_observer["subplot"] is True

    def test_extracts_buysell_observer_markers_from_backtrader_buffers(self):
        class SignalStrategy(bt.Strategy):
            def next(self):
                if not self.position and len(self) == 3:
                    self.buy(size=1)
                elif self.position and len(self) == 6:
                    self.sell(size=1)

        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        closes = [10, 11, 12, 13, 14, 15, 14, 13, 12, 11]
        data = pd.DataFrame(
            {
                "open": closes,
                "high": [value + 1 for value in closes],
                "low": [value - 1 for value in closes],
                "close": closes,
                "volume": [1000] * 10,
            },
            index=dates,
        )

        cerebro = bt.Cerebro()
        cerebro.addstrategy(SignalStrategy)
        cerebro.adddata(bt.feeds.PandasData(dataname=data))
        strat = cerebro.run()[0]

        price_data = [
            {
                "time": date.strftime("%Y-%m-%d"),
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
            }
            for date, row in data.iterrows()
        ]

        chart_data = build_backtest_chart_data(
            strat,
            price_data,
            metrics={"equity_curve": {}, "trade_details": {}},
            initial_cash=10000.0,
        )

        marker_sides = [marker["side"] for marker in chart_data["markers"]]
        assert "buy" in marker_sides
        assert "sell" in marker_sides
