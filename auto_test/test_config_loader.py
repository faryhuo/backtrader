import unittest

from auto_test.test_support import ensure_backend_on_path, reset_session_manager

ensure_backend_on_path()

from src.utils import config_loader


class ConfigLoaderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure any SessionManager state from other tests is cleared.
        reset_session_manager()

    def test_load_broker_config_contains_enabled_exchanges(self) -> None:
        config = config_loader.load_broker_config(reload=True)

        self.assertEqual("1.0", config.version)
        self.assertIn("binance", config.exchanges)

        binance = config.exchanges["binance"]
        self.assertTrue(binance.enabled)
        self.assertEqual("spot", binance.default_market)
        self.assertIn("spot", binance.markets)
        self.assertIn("1m", config.trading_settings.supported_timeframes)

    def test_validation_helpers_enforce_symbol_and_timeframe(self) -> None:
        config = config_loader.load_broker_config(reload=True)

        self.assertTrue(config_loader.validate_symbol("BTC/USDT", "binance", config))
        self.assertTrue(config_loader.validate_timeframe("1h", config))

        with self.assertRaises(ValueError):
            config_loader.validate_symbol("BTCUSDT", "binance", config)

        with self.assertRaises(ValueError):
            config_loader.validate_symbol("BTC/USD/USDT", "binance", config)

        with self.assertRaises(ValueError):
            config_loader.validate_timeframe("2h", config)

    def test_list_enabled_exchanges_reports_paper_mode(self) -> None:
        exchanges = config_loader.list_enabled_exchanges(
            config_loader.load_broker_config(reload=True)
        )

        ids = [ex["id"] for ex in exchanges]
        self.assertIn("binance", ids)

        binance = next(ex for ex in exchanges if ex["id"] == "binance")
        self.assertTrue(binance["paper_mode_available"])
        self.assertIn("spot", binance["markets"])


if __name__ == "__main__":
    unittest.main()
