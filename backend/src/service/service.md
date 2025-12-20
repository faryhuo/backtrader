# service 目录说明

应用服务层目录，承载核心业务编排与运行时资源管理。

## 功能职责（Functional）
- `app.py`：兼容层入口（`app` 实例定义在 `backend/api.py`，此处仅转发导出，供历史导入路径使用）。
- `backtest_engine.py`：回测引擎，支持策略加载、参数解析与回测执行。
- `live_engine.py`：实盘/模拟盘运行引擎与 broker 选择。
- `portfolio_backtest.py`：投资组合回测编排与执行。
- `session_manager.py`：回测/实盘会话生命周期管理。
- `strategy_executor.py`：策略执行编排（统一回测/实盘调用入口、对接沙箱/引擎）。
- `strategy_sandbox.py`：策略代码沙箱执行，安全加载用户策略。
- `isolated_sandbox.py`：更强隔离的策略执行沙箱（进程级隔离等）。
- `strategy_templates.py`：策略模板库管理，提供内置策略模板。
- `version_service.py`：策略版本管理与差异/回滚等服务。
- `walkforward_optimizer.py`：Walk-Forward 参数优化器，训练/验证集分离与过拟合检测。
- `websocket_manager.py`：WebSocket 连接与频道管理。
- `parameter_analysis.py`：策略参数分析/诊断相关能力（供回测/优化流程使用）。
- `deep_analysis.py`：回测深度分析服务，计算月度收益热图、滚动Sharpe、收益/回撤分布、连续亏损统计、基准对比（SPY/沪深300）等高级指标。

## 非功能性要求（Non-Functional）
- 解耦：服务层通过清晰接口调用 DB/适配层，避免直接依赖路由细节。
- 可靠性：对外部 broker/AI/数据源异常做统一封装，便于重试与熔断。
- 可测试性：业务用例应可在 mock 外部依赖下运行。

## 约定与规范
- 服务层不定义路由；路由放 `backend/src/routes`。
- 读取配置统一来自 `backend/src/config/settings.py`。
- 新增长耗时任务需考虑异步/后台执行与取消机制。

