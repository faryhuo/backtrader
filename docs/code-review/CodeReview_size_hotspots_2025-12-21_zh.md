# 大文件 / 长函数 / 大类 全仓扫描（中文）

- 生成日期：2025-12-21
- 统计口径：`git ls-files` + 代码文件后缀 `.py/.js/.jsx/.ts/.tsx`
- 排除目录：`node_modules/`、`frontend/dist/`、`backend/resources/frontend/`、`.git/`
- 阈值：大文件 >= 300 行（高风险 >= 500 行）；Python 函数 >= 80 行（高风险 >= 150 行）；Python 类 >= 200 行（高风险 >= 400 行）

## 1. 概览

- 代码文件总数：225
- 大文件：38（>= 500 行：8）
- Python 长函数：29（>= 150 行：5）
- Python 大类：18（>= 400 行：5）

## 2. 大文件清单（>= 300 行，按行数降序）

| 行数 | 文件 |
|---|---|
| 760 | backend/src/db/storage/settings.py |
| 639 | backend/src/service/deep_analysis.py |
| 560 | frontend/src/pages/BacktestHistory.jsx |
| 560 | backend/src/service/strategy_executor.py |
| 549 | backend/src/service/walkforward_optimizer.py |
| 545 | backend/src/brokers/ccxt_adapter/ccxt_broker.py |
| 534 | backend/src/db/storage/backtest.py |
| 532 | frontend/src/pages/PortfolioBacktest.jsx |
| 499 | backend/src/service/portfolio_backtest.py |
| 493 | backend/src/service/parameter_analysis.py |
| 440 | backend/src/db/storage/walkforward.py |
| 432 | backend/src/routes/live_routes.py |
| 419 | frontend/src/components/WalkForward/WalkForwardDetailModal.jsx |
| 419 | backend/src/service/session_manager.py |
| 415 | frontend/src/pages/RunStrategy.jsx |
| 409 | backend/src/service/backtest_engine.py |
| 406 | backend/tests/service/test_isolated_sandbox.py |
| 401 | backend/src/service/websocket_manager.py |
| 401 | backend/src/routes/settings_routes.py |
| 400 | backend/src/routes/walkforward_routes.py |
| 399 | frontend/src/components/DeepAnalysis/RollingSharpeChart.jsx |
| 393 | backend/src/service/isolated_sandbox.py |
| 385 | backend/src/routes/strategy_routes.py |
| 380 | backend/src/db/storage/session.py |
| 378 | backend/src/service/strategy_templates.py |
| 361 | frontend/src/components/BacktestHistory/PortfolioDetailModal.jsx |
| 360 | backend/src/utils/credential_validator.py |
| 351 | backend/src/config/config_manager.py |
| 348 | frontend/src/pages/StrategyMaintain.jsx |
| 343 | backend/src/utils/config_loader.py |
| 338 | backend/src/service/live_engine.py |
| 336 | frontend/src/components/WalkForward/WalkForwardConfigModal.jsx |
| 330 | backend/src/brokers/ccxt_adapter/ccxt_store.py |
| 325 | backend/src/routes/backtest_routes.py |
| 321 | auto_test/e2e/test_strategy_management.py |
| 316 | frontend/src/components/DeepAnalysis/BenchmarkComparison.jsx |
| 307 | frontend/src/components/WalkForward/WalkForwardOptimization.jsx |
| 305 | backend/src/db/storage/ticker_metadata.py |

## 3. Python 长函数清单（>= 80 行，按行数降序）

| 行数 | 位置 | 函数 |
|---|---|---|
| 254 | backend/src/service/strategy_templates.py:59 | _init_templates |
| 196 | backend/src/routes/websocket_routes.py:22 | websocket_live_updates |
| 190 | backend/src/service/parameter_analysis.py:295 | get_parameter_analysis |
| 170 | backend/src/service/live_engine.py:105 | run_live |
| 167 | backend/src/service/portfolio_backtest.py:249 | run_portfolio_backtest |
| 116 | backend/src/db/storage/market_data.py:39 | save_to_db |
| 114 | backend/src/service/strategy_executor.py:255 | execute_in_sandbox |
| 104 | backend/src/brokers/ccxt_adapter/ccxt_broker.py:362 | _process_filled_order |
| 103 | backend/src/service/portfolio_backtest.py:103 | calculate_optimal_weights |
| 102 | backend/src/service/isolated_sandbox.py:181 | execute_strategy |
| 102 | backend/src/routes/walkforward_routes.py:130 | start_walkforward_optimization |
| 101 | backend/src/service/parameter_analysis.py:91 | build_parameter_grid_matrix |
| 99 | backend/src/service/parameter_analysis.py:194 | calculate_overfitting_score |
| 93 | backend/src/service/strategy_executor.py:160 | _build_safe_builtins |
| 92 | backend/src/service/walkforward_optimizer.py:183 | _run_single_backtest |
| 91 | backend/src/service/deep_analysis.py:532 | compute_benchmark_comparison |
| 91 | backend/src/service/backtest_engine.py:302 | run_backtest |
| 88 | backend/src/routes/live_routes.py:103 | start_live_trading |
| 86 | backend/src/service/walkforward_optimizer.py:343 | run_walkforward |
| 84 | backend/src/utils/credential_validator.py:147 | validate_ccxt_credentials_async |
| 84 | backend/src/service/backtest_engine.py:81 | load_user_strategy |
| 84 | backend/src/db/storage/backtest.py:184 | list_backtests |
| 83 | backend/src/db/storage/settings.py:109 | save_settings |
| 83 | backend/src/db/storage/settings.py:602 | save_ccxt_credentials |
| 81 | backend/src/service/deep_analysis.py:34 | compute_deep_analysis |
| 80 | backend/src/service/deep_analysis.py:450 | compute_consecutive_losses |
| 80 | backend/src/routes/backtest_routes.py:245 | get_or_compute_deep_analysis |
| 80 | backend/src/db/storage/walkforward.py:31 | create_optimization |
| 80 | backend/src/db/storage/backtest.py:37 | save_backtest |

## 4. Python 大类清单（>= 200 行，按行数降序）

| 行数 | 位置 | 类 |
|---|---|---|
| 707 | backend/src/db/storage/settings.py:53 | SettingsStorage |
| 511 | backend/src/db/storage/backtest.py:23 | BacktestStorage |
| 504 | backend/src/brokers/ccxt_adapter/ccxt_broker.py:41 | CCXTBroker |
| 484 | backend/src/service/walkforward_optimizer.py:58 | WalkForwardOptimizer |
| 414 | backend/src/db/storage/walkforward.py:23 | WalkForwardStorage |
| 369 | backend/src/service/websocket_manager.py:18 | WebSocketManager |
| 351 | backend/src/db/storage/session.py:29 | SessionStorage |
| 309 | backend/src/brokers/ccxt_adapter/ccxt_store.py:21 | CCXTStore |
| 303 | backend/src/service/session_manager.py:102 | SessionManager |
| 284 | backend/src/config/config_manager.py:33 | ConfigManager |
| 272 | auto_test/e2e/test_strategy_management.py:25 | TestStrategyAPI |
| 271 | auto_test/libs/data_fixtures.py:15 | DataFixtures |
| 269 | backend/src/service/isolated_sandbox.py:56 | IsolatedSandbox |
| 268 | backend/src/brokers/ccxt_adapter/ccxt_data.py:20 | CCXTData |
| 235 | auto_test/libs/browser_helper.py:18 | BrowserHelper |
| 226 | backend/src/db/storage/strategy_version.py:39 | StrategyVersionStorage |
| 203 | auto_test/e2e/test_backtest_workflow.py:18 | TestBacktestAPI |
| 202 | backend/src/db/storage/portfolio.py:22 | PortfolioStorage |

## 5. 建议（如何拆）

- 大文件：优先按“业务域/分层职责”拆；routes 拆为 `models`（Pydantic）、`handlers`（端点）、`validators`、`dependencies`；service 拆为 `orchestration`（编排）与 `compute`（纯计算）；storage 按領域拆分并保留 fa?ade 聚合。
- 长函数：按阶段拆（`validate -> prepare -> execute -> persist -> format`），每段可独立测试。
- 大类：把“IO/DB/网络/序列化/计算”从一个类里剖离成组件或 helper；类本身保留协调与少量状态。
- 前端说明：本报告只统计文件行数，不可靠解析 JS/JSX 函数边界（避免误报）；但 >300 行页面/组件通常应拆为 `hooks`（数据/副作用） + `components`（展示） + `utils`（纯函数）。