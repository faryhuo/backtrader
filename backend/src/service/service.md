# service 目录说明

应用服务层目录，承载核心业务编排与运行时资源管理。

## 功能职责（Functional）
- `app.py`：兼容层入口（`app` 实例定义在 `backend/api.py`，此处仅转发导出，供历史导入路径使用）。
- `backtest_engine.py`：回测引擎，支持策略加载、参数解析与回测执行。**默认通过 Worker Pool 隔离执行用户代码**。
- `live_engine.py`：实盘/模拟盘运行引擎与 broker 选择。**支持 Worker Pool 隔离执行**。
- `multi_asset_backtest.py`：多资产投资组合回测引擎（含相关性矩阵、Markowitz 优化）。
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

> [!CAUTION]
> **策略代码最终仍在主进程执行**。Worker 进程仅用于**验证阶段**（检测危险模式、资源限制等）。
> 由于 Python 类对象无法跨进程序列化，验证通过后策略代码会在主进程重新执行。
> 
> **此架构仅适用于受信任的策略代码**。公网/多用户场景需要额外的容器隔离层。
> 详见 [docs/SECURITY.md](../../../docs/SECURITY.md)

- 验证隔离：`WORKER_POOL_ENABLED=true`（默认启用）- 在 Worker 进程验证代码安全性
- 跳过验证：`WORKER_POOL_ENABLED=false`（仅用于开发/测试 - **不推荐**）

## 非功能性要求（Non-Functional）
- 解耦：服务层通过清晰接口调用 DB/适配层，避免直接依赖路由细节。
- 可靠性：对外部 broker/AI/数据源异常做统一封装，便于重试与熔断。
- 安全性：用户策略代码在 Worker 进程中隔离执行，支持资源限制（内存、超时）。
- 可测试性：业务用例应可在 mock 外部依赖下运行。

## 编码规范（Tech Requirements）

### 类型注解
- 所有公开函数/方法必须使用 Python 类型注解（Type Hints）。
- 复杂类型使用 `typing` 模块（如 `Optional`, `List`, `Dict`, `Union`）。
- 返回值类型必须明确标注，避免使用 `Any`。

### 文档字符串
- 公开 API 使用 Google 风格 docstring。
- 包含：功能描述、参数说明（`Args`）、返回值（`Returns`）、异常（`Raises`）。

### 异常处理
- 使用自定义异常类（定义于 `backend/src/utils/exceptions.py`）。
- 禁止裸 `except:`，必须捕获具体异常类型。
- 异常信息应包含上下文，便于问题定位。

### 日志规范
- 使用 `backend/src/utils/logger.py` 提供的 logger。
- 日志级别：`DEBUG`（调试）、`INFO`（关键流程）、`WARNING`（潜在问题）、`ERROR`（错误）。
- 敏感信息（密码、token）禁止明文记录。

### 异步编程
- I/O 密集型操作使用 `async/await`。
- CPU 密集型任务委托给 Worker Pool。
- 避免在异步上下文中使用阻塞调用。

## 约定与规范
- 服务层不定义路由；路由放 `backend/src/routes`。
- 读取配置统一来自 `backend/src/config/settings.py`。
- Worker 配置来自 `backend/src/config/worker_config.py`。
- 新增长耗时任务需考虑异步/后台执行与取消机制。
