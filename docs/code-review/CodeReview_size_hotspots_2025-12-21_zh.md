# ??? / ??? / ?? ????????

- ?????2025-12-21
- ?????`git ls-files` + ?????? `.py/.js/.jsx/.ts/.tsx`
- ?????`node_modules/`?`frontend/dist/`?`backend/resources/frontend/`?`.git/`
- ?????? >= 300 ????? >= 500 ???Python ?? >= 80 ????? >= 150 ???Python ? >= 200 ????? >= 400 ??

## 1. ??

- ???????225
- ????36?>= 500 ??8?
- Python ????29?>= 150 ??5?
- Python ???18?>= 400 ??5?

## 2. ??????>= 300 ????????

| ?? | ?? |
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
| 307 | frontend/src/components/WalkForward/WalkForwardOptimization.jsx |
| 305 | backend/src/db/storage/ticker_metadata.py |

## 3. Python ??????>= 80 ????????

| ?? | ?? | ?? |
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

## 4. Python ?????>= 200 ????????

| ?? | ?? | ? |
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

## 5. ???????

- ???????????/???????routes ?? `models`?Pydantic??`handlers`?????`validators`?`dependencies`?service ?? `orchestration`????? `compute`??????storage ???????? fa?ade ???
- ?????????`validate -> prepare -> execute -> persist -> format`????????????
- ?????IO/DB/??/???/?????????????? helper???????????????
- ?????????????????????? JS/JSX ???????????? >300 ???/??????? `hooks`???/????+ `components`????+ `utils`??????