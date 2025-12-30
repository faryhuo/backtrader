"""
Unit tests for sizer configuration module.
"""
import pytest

from src.contracts.sizer_config import (
    SizerType,
    SizerConfig,
    SIZER_TYPE_LABELS,
)


class TestSizerType:
    """Tests for SizerType enum."""

    def test_sizer_type_values(self):
        """Test that all sizer types have correct values."""
        assert SizerType.FIXED_SIZE.value == "fixed_size"
        assert SizerType.PERCENT_SIZER.value == "percent_sizer"
        assert SizerType.ALL_IN_SIZER.value == "all_in_sizer"
        assert SizerType.RISK_SIZER.value == "risk_sizer"
        assert SizerType.KELLY_SIZER.value == "kelly_sizer"

    def test_sizer_type_from_string(self):
        """Test creating SizerType from string value."""
        assert SizerType("fixed_size") == SizerType.FIXED_SIZE
        assert SizerType("percent_sizer") == SizerType.PERCENT_SIZER

    def test_sizer_type_invalid_value(self):
        """Test that invalid sizer type raises ValueError."""
        with pytest.raises(ValueError):
            SizerType("invalid_sizer")


class TestSizerConfig:
    """Tests for SizerConfig Pydantic model."""

    def test_default_values(self):
        """Test default sizer config values."""
        config = SizerConfig()
        assert config.type == SizerType.FIXED_SIZE
        assert config.stake == 100
        assert config.percents == 10.0
        assert config.risk_percent == 2.0

    def test_custom_values(self):
        """Test custom sizer config values."""
        config = SizerConfig(
            type=SizerType.PERCENT_SIZER,
            stake=50,
            percents=20.0,
            risk_percent=5.0,
        )
        assert config.type == SizerType.PERCENT_SIZER
        assert config.stake == 50
        assert config.percents == 20.0
        assert config.risk_percent == 5.0

    def test_to_dict(self):
        """Test converting sizer config to dictionary."""
        config = SizerConfig(
            type=SizerType.RISK_SIZER,
            stake=100,
            percents=15.0,
            risk_percent=3.0,
        )
        d = config.to_dict()
        assert d["type"] == "risk_sizer"
        assert d["stake"] == 100
        assert d["percents"] == 15.0
        assert d["risk_percent"] == 3.0

    def test_from_dict_full(self):
        """Test creating sizer config from full dictionary."""
        data = {
            "type": "kelly_sizer",
            "stake": 200,
            "percents": 25.0,
            "risk_percent": 4.0,
        }
        config = SizerConfig.from_dict(data)
        assert config.type == SizerType.KELLY_SIZER
        assert config.stake == 200
        assert config.percents == 25.0
        assert config.risk_percent == 4.0

    def test_from_dict_partial(self):
        """Test creating sizer config from partial dictionary."""
        data = {"type": "percent_sizer"}
        config = SizerConfig.from_dict(data)
        assert config.type == SizerType.PERCENT_SIZER
        # Other values should be defaults
        assert config.stake == 100
        assert config.percents == 10.0

    def test_from_dict_none(self):
        """Test creating sizer config from None."""
        config = SizerConfig.from_dict(None)
        assert config.type == SizerType.FIXED_SIZE
        assert config.stake == 100

    def test_from_dict_empty(self):
        """Test creating sizer config from empty dictionary."""
        config = SizerConfig.from_dict({})
        assert config.type == SizerType.FIXED_SIZE

    def test_from_dict_with_sizer_type_enum(self):
        """Test creating sizer config with SizerType enum in dict."""
        data = {
            "type": SizerType.ALL_IN_SIZER,
            "stake": 100,
        }
        config = SizerConfig.from_dict(data)
        assert config.type == SizerType.ALL_IN_SIZER

    def test_stake_validation_min(self):
        """Test that stake must be at least 1."""
        with pytest.raises(ValueError):
            SizerConfig(stake=0)

    def test_percents_validation_range(self):
        """Test that percents must be between 0.1 and 100."""
        # Valid range
        config = SizerConfig(percents=0.1)
        assert config.percents == 0.1
        
        config = SizerConfig(percents=100.0)
        assert config.percents == 100.0

    def test_risk_percent_validation_range(self):
        """Test that risk_percent must be between 0.1 and 100."""
        config = SizerConfig(risk_percent=0.1)
        assert config.risk_percent == 0.1


class TestSizerTypeLabels:
    """Tests for sizer type display labels."""

    def test_all_sizer_types_have_labels(self):
        """Test that all sizer types have corresponding labels."""
        for sizer_type in SizerType:
            assert sizer_type in SIZER_TYPE_LABELS

    def test_label_values(self):
        """Test specific label values."""
        assert SIZER_TYPE_LABELS[SizerType.FIXED_SIZE] == "Fixed Size"
        assert SIZER_TYPE_LABELS[SizerType.PERCENT_SIZER] == "Percent Sizer"
        assert SIZER_TYPE_LABELS[SizerType.ALL_IN_SIZER] == "All In Sizer"
        assert SIZER_TYPE_LABELS[SizerType.RISK_SIZER] == "Risk Sizer"
        assert SIZER_TYPE_LABELS[SizerType.KELLY_SIZER] == "Kelly Criterion"
