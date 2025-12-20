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
- `market_data_routes.py`：市场数据
  - `/api/ticker/{ticker}/info` - 标的信息
  - `/api/ticker/{ticker}/prices` - 价格数据
  - `/api/data` - 兼容旧接口
  - `/api/analyze` - 基础分析

### 其他路由模块
- `ai_routes.py`：AI 分析接口（`/api/ai_analyze`），集成 OpenAI 进行回测结果分析。
- `frontend_routes.py`：静态资源挂载与前端路由托管。
- `live_routes.py`：实盘/模拟盘交易接口（`/api/live/*`），会话管理与交易操作。
- `portfolio_routes.py`：投资组合回测接口（`/api/portfolio/*`）。
- `settings_routes.py`：用户设置与凭证管理接口（`/api/settings/*`）。
- `walkforward_routes.py`：Walk-Forward 参数优化接口（`/api/walkforward/*`）。
- `websocket_routes.py`：WebSocket 实时推送接口，交易状态与系统事件广播。

## 非功能性要求（Non-Functional）
- 一致性：错误码/响应结构统一，便于前端与监控消费。
- 安全：在路由层做鉴权与权限检查，避免未授权访问。
- 可维护性：路由只做编排，不直接操作 DB 或外部 broker。

## 约定与规范
- 新路由文件命名为 `{feature}_routes.py`，对外暴露 `router`。
- 路由注册统一在 `backend/api.py` 完成（该文件负责 `include_router(...)` 与 CORS/异常处理配置）。
- 接口变更需同步更新前端 `frontend/src/services/api.js` 及文档示例。
- 大型路由文件应按领域拆分为子模块，避免单文件过大与跨域耦合。

