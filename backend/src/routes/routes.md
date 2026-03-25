# routes 目录说明

FastAPI 路由与接口层目录，集中维护 HTTP/WebSocket API。

## 文件结构与注册方式

本目录下每个 `{feature}_routes.py` 负责声明 `APIRouter`（参数校验、响应编排、权限检查），由后端入口统一注册：

- 路由注册位置：`backend/api.py`
- 前端静态资源托管：`frontend_routes.py` 提供 `mount_frontend(app)`

说明：当前项目不再使用 `api_routes.py` 作为聚合器；各路由模块由 `backend/api.py` 直接 `include_router(...)`。

### 核心 API 路由（按领域拆分）
- `strategy_routes.py`：策略管理（CRUD、模板、版本控制）
  - `/api/strategies` - 策略列表
  - `/api/strategy` - 策略 CRUD
  - `/api/strategy/{name}/params` - 策略参数
  - `/api/strategy/{name}/versions` - 版本管理
  - `/api/templates` - 策略模板/导入
- `backtest_routes.py`：回测执行与历史
  - `/api/backtest` - 执行回测
  - `/api/backtest/history` - 回测历史管理
  - `/api/backtest/history/{id}/ai-analysis` - AI 分析更新
  - `/api/backtest/history/{id}/deep-analysis` - 深度分析（月度收益热图、滚动Sharpe、收益分布、回撤分析、连续亏损、基准对比）
- `market_data_routes.py`：市场数据
  - `/api/ticker/{ticker}/info` - 标的信息
  - `/api/ticker/{ticker}/prices` - 价格数据
  - `/api/data` - 兼容旧接口
  - `/api/analyze` - 基础分析

### 其他路由模块
- `ai_routes.py`：AI 分析接口（`/api/ai_analyze`），通过统一 AI service 调用多 provider 并支持优先级回退。
- `frontend_routes.py`：静态资源挂载与前端路由托管。
- `live_routes.py`：实盘/模拟盘交易接口（`/api/live/*`），会话管理与交易操作。
- `portfolio_routes.py`：投资组合回测接口（`/api/portfolio/*`）。
- `settings_routes.py`：用户设置与凭证管理接口（`/api/settings/*`）。
- `walkforward_routes.py`：Walk-Forward 参数优化接口（`/api/walkforward/*`）。
- `websocket_routes.py`：WebSocket 实时推送接口，交易状态与系统事件广播。

- `settings_routes.py` now exposes unified AI model provider settings instead of a single OpenAI-only credential pair.
- `ai_routes.py` now delegates to the unified AI service and supports ordered provider fallback across OpenAI, MiniMax, Gemini, and Claude.

## 非功能性要求（Non-Functional）
- 一致性：错误码/响应结构统一，便于前端与监控消费。
- 安全：在路由层做鉴权与权限检查，避免未授权访问。
- 可维护性：路由只做编排，不直接操作 DB 或外部 broker。

## 编码规范（Tech Requirements）

### 类型注解
- 所有路由函数必须使用 Python 类型注解（Type Hints）。
- 请求体使用 Pydantic 模型定义，确保自动验证与文档生成。
- 返回值类型必须明确标注，推荐使用 `Response` 或具体 Pydantic 模型。

### 请求验证
- 使用 Pydantic 模型进行请求体验证（`Body`, `Query`, `Path`）。
- 路径参数和查询参数使用 FastAPI 的类型注解自动验证。
- 复杂验证逻辑使用 Pydantic 的 `validator` 或 `field_validator`。

### 响应格式
- 统一响应结构：`{"success": bool, "data": any, "error": str | null}`。
- 错误响应使用 `HTTPException`，包含明确的 `status_code` 和 `detail`。
- 分页响应使用统一格式：`{"items": [], "total": int, "page": int, "page_size": int}`。

### 异常处理
- 路由层异常由全局异常处理器捕获（配置于 `backend/api.py`）。
- 业务异常使用 `backend/src/utils/exceptions.py` 中的自定义异常类。
- 禁止在路由中暴露内部错误堆栈，生产环境返回通用错误信息。

### 日志规范
- 使用 `backend/src/utils/logger.py` 提供的 logger。
- 记录关键请求信息：端点、用户、耗时、状态码。
- 敏感信息（密码、token、API Key）禁止明文记录。

### 安全要求
- 需要认证的端点使用 `Depends(get_current_user)` 依赖注入。
- 敏感操作（删除、修改配置）需额外权限检查。
- 用户输入必须验证和清理，防止注入攻击。

### 异步编程
- 路由函数使用 `async def` 定义，充分利用 FastAPI 异步能力。
- 调用服务层时使用 `await`，避免阻塞事件循环。
- 长耗时操作使用后台任务（`BackgroundTasks`）或 Worker Pool。

## 约定与规范
- 新路由文件命名为 `{feature}_routes.py`，对外暴露 `router`。
- 路由注册统一在 `backend/api.py` 完成（该文件负责 `include_router(...)` 与 CORS/异常处理配置）。
- 接口变更需同步更新前端 `frontend/src/services/api.js` 及文档示例。
- 大型路由文件应按领域拆分为子模块，避免单文件过大与跨域耦合。

