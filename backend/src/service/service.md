# service 目录说明

应用服务层目录，承载核心业务编排与运行时资源管理。

## 功能职责（Functional）
- `app.py`：FastAPI 应用创建、路由注册与中间件配置。
- `live_engine.py`：实盘/模拟盘运行引擎与 broker 选择。
- `session_manager.py`：回测/实盘会话生命周期管理。
- `websocket_manager.py`：WebSocket 连接与频道管理。

## 非功能性要求（Non-Functional）
- 解耦：服务层通过清晰接口调用 DB/适配层，避免直接依赖路由细节。
- 可靠性：对外部 broker/AI/数据源异常做统一封装，便于重试与熔断。
- 可测试性：业务用例应可在 mock 外部依赖下运行。

## 约定与规范
- 服务层不定义路由；路由放 `backend/src/routes`。
- 读取配置统一来自 `backend/src/config/settings.py`。
- 新增长耗时任务需考虑异步/后台执行与取消机制。

