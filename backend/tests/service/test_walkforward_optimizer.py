from src.service.walkforward_optimizer import WalkForwardOptimizer


def test_generate_param_combinations():
    """Test that parameter combinations are generated correctly from param_grid."""
    optimizer = WalkForwardOptimizer(
        strategy_name="s",
        ticker="AAPL",
        start_date="2024-01-01",
        end_date="2024-02-01",
        param_grid={"a": [1, 2], "b": ["x"]},
        train_period_days=10,
        test_period_days=5,
        anchored=False,
    )
    combos = optimizer._generate_param_combinations()
    assert {"a": 1, "b": "x"} in combos
    assert {"a": 2, "b": "x"} in combos


def test_generate_windows_rolling_vs_anchored():
    """Test that rolling and anchored windows are generated correctly."""
    rolling = WalkForwardOptimizer(
        strategy_name="s",
        ticker="AAPL",
        start_date="2024-01-01",
        end_date="2024-02-15",
        param_grid={},
        train_period_days=10,
        test_period_days=5,
        anchored=False,
    )
    rw = rolling._generate_windows()
    assert len(rw) >= 1

    anchored = WalkForwardOptimizer(
        strategy_name="s",
        ticker="AAPL",
        start_date="2024-01-01",
        end_date="2024-02-15",
        param_grid={},
        train_period_days=10,
        test_period_days=5,
        anchored=True,
    )
    aw = anchored._generate_windows()
    assert len(aw) >= 1

