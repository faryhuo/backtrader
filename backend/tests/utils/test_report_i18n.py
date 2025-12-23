"""
Unit tests for report i18n utilities.
"""
import pytest

from src.utils.report_i18n import (
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    TRANSLATIONS,
    get_translations,
    get_report_type_name,
)


class TestTranslationConstants:
    """Tests for translation constants."""

    def test_supported_languages(self):
        """Test that supported languages are defined."""
        assert SUPPORTED_LANGUAGES == ["en", "zh"]
        assert len(SUPPORTED_LANGUAGES) == 2

    def test_default_language(self):
        """Test that default language is English."""
        assert DEFAULT_LANGUAGE == "en"
        assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGES

    def test_translations_structure(self):
        """Test that translations dictionary has correct structure."""
        assert isinstance(TRANSLATIONS, dict)
        assert "en" in TRANSLATIONS
        assert "zh" in TRANSLATIONS

        # Verify each language has a dictionary of translations
        for lang in SUPPORTED_LANGUAGES:
            assert isinstance(TRANSLATIONS[lang], dict)
            assert len(TRANSLATIONS[lang]) > 0


class TestGetTranslations:
    """Tests for get_translations function."""

    def test_get_english_translations(self):
        """Test getting English translations."""
        translations = get_translations("en")

        assert translations["lang"] == "en"
        assert "report_type" in translations
        assert "backtest" in translations
        assert "tab_overview" in translations

    def test_get_chinese_translations(self):
        """Test getting Chinese translations."""
        translations = get_translations("zh")

        assert translations["lang"] == "zh"
        assert "report_type" in translations
        assert "backtest" in translations
        assert "tab_overview" in translations

    def test_get_default_language_on_invalid(self):
        """Test that invalid language code returns default language."""
        translations = get_translations("fr")  # Unsupported language

        assert translations["lang"] == "en"

    def test_get_default_language_on_empty(self):
        """Test that empty language code returns default language."""
        translations = get_translations("")

        assert translations["lang"] == "en"

    def test_translations_have_same_keys(self):
        """Test that all languages have the same translation keys."""
        en_keys = set(TRANSLATIONS["en"].keys())
        zh_keys = set(TRANSLATIONS["zh"].keys())

        # Both should have the same keys
        assert en_keys == zh_keys


class TestGetReportTypeName:
    """Tests for get_report_type_name function."""

    def test_get_backtest_name_english(self):
        """Test getting backtest report type name in English."""
        name = get_report_type_name("backtest", "en")

        assert name == "Backtest"

    def test_get_backtest_name_chinese(self):
        """Test getting backtest report type name in Chinese."""
        name = get_report_type_name("backtest", "zh")

        assert name == "回测"

    def test_get_portfolio_name_english(self):
        """Test getting portfolio report type name in English."""
        name = get_report_type_name("portfolio", "en")

        assert name == "Portfolio"

    def test_get_portfolio_name_chinese(self):
        """Test getting portfolio report type name in Chinese."""
        name = get_report_type_name("portfolio", "zh")

        assert name == "组合"

    def test_get_walkforward_name_english(self):
        """Test getting walkforward report type name in English."""
        name = get_report_type_name("walkforward", "en")

        assert name == "Walk-Forward"

    def test_get_comparison_name_english(self):
        """Test getting comparison report type name in English."""
        name = get_report_type_name("comparison", "en")

        assert name == "Comparison"

    def test_get_unknown_report_type(self):
        """Test that unknown report types return capitalized version."""
        name = get_report_type_name("unknown_type", "en")

        assert name == "Unknown_type"

    def test_get_report_type_default_language(self):
        """Test that default language parameter works correctly."""
        # When no language is specified, should use default
        name1 = get_report_type_name("backtest")
        name2 = get_report_type_name("backtest", "en")

        assert name1 == name2


class TestTranslationContent:
    """Tests for translation content completeness."""

    def test_english_has_core_keys(self):
        """Test that English translations have all core keys."""
        en = TRANSLATIONS["en"]

        # Core labels
        assert "lang" in en
        assert "report_type" in en
        assert "generated" in en
        assert "strategy" in en
        assert "symbol" in en

        # Report types
        assert "backtest" in en
        assert "portfolio" in en
        assert "walkforward" in en
        assert "comparison" in en

        # Performance metrics
        assert "final_value" in en
        assert "total_return" in en
        assert "sharpe_ratio" in en
        assert "max_drawdown" in en

    def test_chinese_has_core_keys(self):
        """Test that Chinese translations have all core keys."""
        zh = TRANSLATIONS["zh"]

        # Core labels
        assert "lang" in zh
        assert "report_type" in zh
        assert "generated" in zh
        assert "strategy" in zh
        assert "symbol" in zh

        # Report types
        assert "backtest" in zh
        assert "portfolio" in zh
        assert "walkforward" in zh
        assert "comparison" in zh

        # Performance metrics
        assert "final_value" in zh
        assert "total_return" in zh
        assert "sharpe_ratio" in zh
        assert "max_drawdown" in zh

    def test_tab_translations(self):
        """Test that all tab translations exist."""
        tabs = [
            "tab_overview",
            "tab_charts",
            "tab_trades",
            "tab_parameters",
            "tab_deep_analysis",
            "tab_ai_analysis",
        ]

        for lang in SUPPORTED_LANGUAGES:
            translations = TRANSLATIONS[lang]
            for tab in tabs:
                assert tab in translations

    def test_table_header_translations(self):
        """Test that all table header translations exist."""
        headers = [
            "entry_date",
            "exit_date",
            "type",
            "size",
            "entry_price",
            "exit_price",
            "pnl",
            "return_pct",
        ]

        for lang in SUPPORTED_LANGUAGES:
            translations = TRANSLATIONS[lang]
            for header in headers:
                assert header in translations

    def test_no_empty_translations(self):
        """Test that no translations are empty strings."""
        for lang in SUPPORTED_LANGUAGES:
            translations = TRANSLATIONS[lang]
            for key, value in translations.items():
                assert value != "", f"Empty translation for key '{key}' in language '{lang}'"


class TestTranslationUsage:
    """Tests for typical usage patterns."""

    def test_use_translations_in_template_context(self):
        """Test using translations in a template context."""
        t = get_translations("en")

        # Simulate template context usage
        context = {
            "report_type_label": t["report_type"],
            "performance_title": t["performance_overview"],
            "tabs": [
                {"id": "overview", "name": t["tab_overview"]},
                {"id": "charts", "name": t["tab_charts"]},
                {"id": "trades", "name": t["tab_trades"]},
            ]
        }

        assert context["report_type_label"] == "Report Type"
        assert context["performance_title"] == "Performance Overview"
        assert len(context["tabs"]) == 3
        assert context["tabs"][0]["name"] == "Overview"

    def test_fallback_for_missing_key(self):
        """Test that missing keys can be handled with .get()."""
        t = get_translations("en")

        # Use .get() with fallback for missing keys
        value = t.get("nonexistent_key", "N/A")

        assert value == "N/A"

    def test_switching_languages(self):
        """Test switching between languages dynamically."""
        # Start with English
        t_en = get_translations("en")
        assert t_en["total_return"] == "Total Return"

        # Switch to Chinese
        t_zh = get_translations("zh")
        assert t_zh["total_return"] == "总收益率"

        # Verify they're different
        assert t_en["total_return"] != t_zh["total_return"]


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_none_language(self):
        """Test that None language returns default."""
        # The function handles None gracefully and returns default language
        translations = get_translations(None)
        # Since None is not in SUPPORTED_LANGUAGES, it returns default
        assert translations["lang"] == "en"

    def test_case_sensitivity(self):
        """Test that language codes are case-sensitive."""
        # Uppercase should fallback to default
        translations = get_translations("EN")

        assert translations["lang"] == "en"  # Falls back to default

    def test_special_characters_in_translations(self):
        """Test that special characters in translations are preserved."""
        zh = TRANSLATIONS["zh"]

        # Chinese translations should have Chinese characters
        assert "回测" in zh["backtest"]
        assert "%" not in zh["total_return"]  # Should be in Chinese


class TestAllKeysPresent:
    """Comprehensive test that all expected keys are present."""

    def test_all_expected_keys_present(self):
        """Test that a comprehensive list of expected keys exist."""
        expected_keys = {
            # Language
            "lang",
            # Header labels
            "report_type", "generated", "strategy", "symbol", "period",
            # Report types
            "backtest", "portfolio", "walkforward", "comparison",
            # Tabs
            "tab_overview", "tab_charts", "tab_trades", "tab_parameters",
            "tab_deep_analysis", "tab_ai_analysis",
            # Metrics
            "final_value", "total_return", "sharpe_ratio", "max_drawdown",
            "total_trades", "win_rate", "profit_factor", "sqn",
            # Sections
            "performance_overview", "annual_returns", "equity_curve",
            "trade_summary", "strategy_params",
            # Table headers
            "year", "return", "entry_date", "exit_date", "type", "size",
            "entry_price", "exit_price", "pnl", "return_pct",
            # Config
            "start_date", "end_date", "initial_cash", "commission", "stake",
            # Misc
            "no_data", "trading_report",
        }

        for lang in SUPPORTED_LANGUAGES:
            translations = TRANSLATIONS[lang]
            for key in expected_keys:
                assert key in translations, f"Missing key '{key}' in language '{lang}'"
