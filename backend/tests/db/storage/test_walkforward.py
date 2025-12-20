from src.db.storage.walkforward import WalkForwardStorage
from src.service.walkforward_optimizer import OptimizationWindow, WalkForwardResult


def test_walkforward_storage_create_update_and_save_result(tmp_path):
    db_path = (tmp_path / "wf.sqlite").as_posix()
    storage = WalkForwardStorage(f"sqlite:///{db_path}")

    storage.create_optimization(
        optimization_id="o1",
        strategy_name="strat",
        ticker="AAPL",
        start_date="2024-01-01",
        end_date="2024-12-31",
        param_grid={"p": [1, 2]},
        train_period_days=10,
        test_period_days=5,
        anchored=False,
        optimization_metric="total_return",
        initial_cash=1000.0,
        commission=0.0,
        stake=1,
        user_id="u1",
    )

    assert storage.update_optimization_status("o1", "running") is True

    result = WalkForwardResult(
        optimization_id="o1",
        strategy_name="strat",
        ticker="AAPL",
        total_start_date="2024-01-01",
        total_end_date="2024-12-31",
        windows=[
            OptimizationWindow(
                window_id=1,
                train_start="2024-01-01",
                train_end="2024-01-10",
                test_start="2024-01-11",
                test_end="2024-01-15",
                best_params={"p": 1},
                train_metrics={"total_return": 1.0},
                test_metrics={"total_return": 0.5},
            )
        ],
        param_grid={"p": [1, 2]},
        overfitting_metrics={"avg_train_performance": 1.0, "avg_test_performance": 0.5, "overfitting_detected": False},
        combined_test_metrics={"total_return": 0.5},
    )

    saved = storage.save_optimization_result(result, user_id="u1")
    assert saved.optimization_id == "o1"
    assert saved.status == "completed"

