# service 目录说明

应用服务层目录，承载核心业务编排与运行时资源管理。

## 功能职责（Functional）
- `app.py`：兼容层入口（`app` 实例定义在 `backend/api.py`，此处仅转发导出，供历史导入路径使用）。
- `backtest_engine.py`：回测引擎，支持策略加载、参数解析与回测执行。**默认通过 Worker Pool 隔离执行用户代码**。
- `live_engine.py`：实盘/模拟盘运行引擎与 broker 选择。**支持 Worker Pool 隔离执行**。
- `portfolio_backtest.py`：投资组合回测编排与执行。
- `session_manager.py`：回测/实盘会话生命周期管理。
- `strategy_executor.py`：策略执行编排（统一回测/实盘调用入口、对接沙箱/引擎）。
- `strategy_sandbox.py`：策略代码沙箱执行，安全加载用户策略（软隔离）。
- `isolated_sandbox.py`：更强隔离的策略执行沙箱（进程级隔离，用于参数提取等）。
- `strategy_templates.py`：策略模板库管理，提供内置策略模板。
- `version_service.py`：策略版本管理与差异/回滚等服务。
- `walkforward_optimizer.py`：Walk-Forward 参数优化器，训练/验证集分离与过拟合检测。**通过 `run_backtest()` 使用 Worker Pool**。
- `websocket_manager.py`：WebSocket 连接与频道管理。
- `parameter_analysis.py`：策略参数分析/诊断相关能力（供回测/优化流程使用）。
- `deep_analysis.py`：回测深度分析服务，计算月度收益热图、滚动Sharpe、收益/回撤分布、连续亏损统计、基准对比（SPY/沪深300）等高级指标。
- `worker/`：**Worker 进程池模块**，提供隔离的策略代码执行环境（详见 [worker/worker.md](worker/worker.md)）。

## 安全架构

> **重要**：主进程（API 进程）**不再直接执行**用户策略代码。
> 所有 `exec/compile` 操作都在隔离的 Worker 进程中进行。

- 启用方式：`WORKER_POOL_ENABLED=true`（默认启用）
- 禁用方式：`WORKER_POOL_ENABLED=false`（仅用于开发/测试）

## 非功能性要求（Non-Functional）
- 解耦：服务层通过清晰接口调用 DB/适配层，避免直接依赖路由细节。
- 可靠性：对外部 broker/AI/数据源异常做统一封装，便于重试与熔断。
- 安全性：用户策略代码在 Worker 进程中隔离执行，支持资源限制（内存、超时）。
- 可测试性：业务用例应可在 mock 外部依赖下运行。

## 约定与规范
- 服务层不定义路由；路由放 `backend/src/routes`。
- 读取配置统一来自 `backend/src/config/settings.py`。
- Worker 配置来自 `backend/src/config/worker_config.py`。
- 新增长耗时任务需考虑异步/后台执行与取消机制。
