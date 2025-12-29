# Code Review：代码冗余与可维护性问题清单（2025-12-29）

- 仓库版本：`ec24ba6`
- 审查范围：仅关注代码实现层面的“冗余/重复实现/难维护”问题（不评价业务正确性）
- 覆盖目录：`backend/`（重点 `backend/src/` + `backend/api.py`/`backend/main.py`），`frontend/src/`

## 代码体积热点（文件过大=维护风险）
### Backend
| 文件 | 行数 |
|---|---:|
| `backend/src/service/worker/worker_pool.py` | 921 |
| `backend/src/service/report_generator.py` | 568 |
| `backend/src/service/strategy_executor.py` | 529 |
| `backend/src/service/deep_analysis.py` | 528 |
| `backend/src/service/multi_asset_backtest.py` | 521 |
| `backend/src/routes/backtest_routes.py` | 497 |
| `backend/src/service/parameter_analysis.py` | 477 |
| `backend/src/service/portfolio_optimizer.py` | 471 |
| `backend/src/service/walkforward_optimizer.py` | 453 |
| `backend/src/service/live_engine.py` | 442 |

### Frontend
| 文件 | 行数 |
|---|---:|
| `frontend/src/components/WalkForward/WalkForwardDetailModal.jsx` | 496 |
| `frontend/src/components/WalkForward/WalkForwardConfigModal.jsx` | 398 |
| `frontend/src/pages/TaskCenter.jsx` | 379 |
| `frontend/src/components/BacktestHistory/BacktestDetailModal.jsx` | 374 |
| `frontend/src/components/RunStrategy/StrategyConfigForm.jsx` | 361 |
| `frontend/src/pages/ReportCenter.jsx` | 342 |
| `frontend/src/pages/StrategyMaintain.jsx` | 328 |

## 主要问题清单（按优先级）
### P0：跨模块数据结构/字段命名不统一，导致重复转换与潜在缺陷
- `equity_curve` 表示不一致：`backend/src/service/deep_analysis.py` 期望 `Dict[datetime, float]`，但 `backend/src/service/worker/backtest_worker.py`/`backend/src/service/pyfolio_exporter.py` 实际使用 `Dict[str, float]`（日期字符串）。
- `trade_details.trades` 字段命名不一致：`backend/src/service/backtest_engine.py` 产出的 trade 字段偏向 `open_date/open_price/close_date/close_price`，而 `backend/src/service/pyfolio_exporter.py`、`backend/src/service/report_generator.py` 读取时使用 `entry_date/entry_price/exit_date/exit_price`。
- 维护成本：同一份数据在不同模块需要“猜测/兼容/转换”，一旦字段调整会引发连锁修改。
- 建议：定义一份权威的结果 schema（含字段命名与类型），在“落库前”或“服务层出口”集中 `normalize()`；前端只消费规范化结构。

### P0：Backtrader analyzers 配置与指标抽取重复散落，且指标集合/命名易漂移
- 证据：
  - `backend/src/service/backtest_runner.py#run_backtest_legacy()`
  - `backend/src/service/worker/backtest_worker.py#execute_backtest_task()`
  - `backend/src/service/worker/live_worker.py#LiveWorkerSession._run_session()`
  - `backend/src/service/live_engine.py`（同类逻辑）
- 问题：多处重复 `cerebro.addanalyzer(...)` + 指标抽取；不同路径添加的 analyzer/输出字段不一致（例如 worker 增加 `calmar/vwr`，legacy 未必一致）。
- 建议：抽出 `configure_analyzers(cerebro, mode=...)` + `extract_metrics(strat, broker)`，并做统一的字段命名（例如全部用 `sharpe_ratio/max_drawdown/total_return` 或统一映射层）。

### P1：任务 executor 样板代码在多个 routes 复制，且 config/result 映射多份
- 证据：
  - `backend/src/routes/backtest_routes.py#_backtest_executor()`
  - `backend/src/routes/portfolio_routes.py#_multi_asset_executor()`
  - `backend/src/routes/walkforward_routes.py#_walkforward_executor()`
  - `backend/src/routes/common/task_helpers.py#create_task_config()`
- 问题：重复 `asyncio.get_event_loop()->run_in_executor(partial(...))`；同一份配置字段在 request model / `create_task_config` / executor 调用 / storage 落库之间多次手写映射，容易“漂移”。
- 建议：将 task_type→executor 的注册表与 config 构建收敛到 `service/`；routes 只做校验+提交；并提供通用 `run_blocking_in_threadpool(func, *args, **kwargs)` 工具。

### P1：默认参数/常量散落后端与前端，多处硬编码易不一致
- 证据：`commission=0.0005`、`initial_cash=100000`、`timeframe="1d"`、`stake=100` 分别出现在：
  - `backend/src/routes/backtest_routes.py`、`backend/src/routes/walkforward_routes.py`、`backend/src/routes/portfolio_routes.py`
  - `backend/src/service/backtest_engine.py`、`backend/src/service/worker/task_models.py`
  - `backend/src/db/models/backtest.py`、`backend/src/db/storage/backtest.py`
  - `frontend/src/pages/RunStrategy.jsx`、`frontend/src/pages/PortfolioBacktest.jsx`、`frontend/src/components/WalkForward/WalkForwardConfigModal.jsx`
- 建议：集中定义 defaults（例如 `backend/src/contracts/constants.py`），并通过站点配置接口下发到前端；至少避免前端再硬编码同一组默认值。

### P1：DB 会话管理/访问方式不统一，导致重复样板与边界行为不一致
- 证据：
  - `backend/src/db/storage/base.py` 同时存在 `session_scope()`、`managed_session()`、`_manage_session()`（三套入口）
  - `backend/src/db/storage/data_cache.py` 走 `_manage_session()` + 手动 close
  - `backend/src/db/storage/market_data.py` 走模块级全局 `_ENGINE/_SESSION_LOCAL`
- 问题：不同模块提交/回滚/关闭行为不一致；新同学难以判断应使用哪套；也更难写统一测试。
- 建议：统一为 `BaseStorage.managed_session()`（或保留一套），逐步收敛 `market_data.py` 到 storage 类（避免模块级全局状态）。

### P2：WorkerPool 模块过大且 worker main loop 代码高度重复
- 证据：`backend/src/service/worker/worker_pool.py`（921 行），`_backtest_worker_main()` / `_multi_asset_worker_main()` / `_live_worker_main()` 主循环结构相似。
- 建议：抽象通用循环（取任务→执行→回传结果→错误包装），并拆分进程管理/队列收集/心跳等子模块，降低修改风险。

### P2：导入期副作用（mkdir/ensure dirs）分散，降低可预测性与可测试性
- 证据：
  - `backend/api.py` import 时调用 `ensure_resource_dirs()`
  - `backend/src/config/settings.py#_build_sqlite_url()` 构造 DB URL 时 `mkdir`
  - `backend/src/service/report_generator.py` 模块顶层 `mkdir`
- 建议：统一移动到 FastAPI `startup/lifespan` 阶段；导入期尽量保持纯计算，避免写磁盘。

### P2：Settings/Credentials 字段 flatten/unflatten 纯手工映射，字段增删成本高
- 证据：`backend/src/routes/settings_routes.py#get_credentials()` 手动拼 `credentials_flat` 与 `sources`。
- 维护成本：新增字段需要同时改“后端 mapping + 前端表单/Hook + 校验/测试”，容易遗漏。
- 建议：用一份字段映射表（常量）自动生成；或前后端直接使用 nested schema（减少双向映射）。

### P3：存在未被使用的异常体系/工具层，增加噪音与分歧点
- 证据：`backend/src/utils/exception_handlers.py` 定义 `AppError` 及大量子类，但仓库内几乎没有使用点（仅此文件内引用）。
- 建议：要么在 service 层统一改用该异常体系，要么删除/合并为更小的工具，减少“多套异常体系”造成的维护成本。

## Frontend 侧主要问题
### P1：单文件过大且混合职责（数据获取/整形/业务规则/渲染）
- 证据（行数热点）：
  - `frontend/src/components/WalkForward/WalkForwardDetailModal.jsx`（496）
  - `frontend/src/components/WalkForward/WalkForwardConfigModal.jsx`（398）
  - `frontend/src/pages/TaskCenter.jsx`（379）
  - `frontend/src/components/BacktestHistory/BacktestDetailModal.jsx`（374）
  - `frontend/src/components/RunStrategy/StrategyConfigForm.jsx`（361）
- 建议：拆分 Container（数据/状态）与 Presentational（纯 UI）；把数据整形/阈值规则下沉到 hooks/utils；复用 `utils/tableColumns/*`。

### P2：数值/百分比格式化在组件内重复实现（已有统一工具未充分复用）
- 证据：大量 `toFixed()`、`%` 拼接散落在多个组件（例如 `WalkForwardDetailModal.jsx`、`WalkForwardOptimization.jsx`、`ReturnsDistribution.jsx` 等），而项目已有 `frontend/src/utils/formatters.js`。
- 建议：统一使用 `formatNumber/formatPercent/formatCurrency`，并把阈值/颜色规则抽成常量或小函数。

### P2：直接修改 props 对象导致状态难追踪
- 证据：`frontend/src/components/BacktestHistory/BacktestDetailModal.jsx` 中直接执行 `backtest.ai_analysis = ...`。
- 影响：React 语义上 props 应视为只读；直接 mutation 容易引入父子状态不同步与难复现 bug。
- 建议：通过回调把更新交给父组件，或在 Modal 内维护局部 state 并在保存后触发刷新。

---

## 建议的落地顺序（最小投入/最大收益）
1. 统一结果 schema（`equity_curve`/`trade_details`/指标字段命名）并集中 normalize
2. 抽离 Backtrader analyzers 配置与 metrics 抽取，减少多路径漂移
3. 收敛 routes 的 executor 样板与 defaults 常量
4. 统一 DB session 管理与 market_data 访问方式
5. 拆分 WorkerPool 与前端大组件，提升可读性与可测试性
