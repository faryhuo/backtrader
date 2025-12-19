# routes 目录说明

FastAPI 路由与接口层目录，集中维护 HTTP/WebSocket API。

## 功能职责（Functional）
- `ai_routes.py`：AI 分析接口（`/api/ai_analyze`），集成 OpenAI 进行回测结果分析。
- `api_routes.py`：核心 API 路由（`/api/backtest`、`/api/strategy`、`/api/data`），策略管理与回测执行。
- `frontend_routes.py`：静态资源挂载与前端路由托管。
- `live_routes.py`：实盘/模拟盘交易接口（`/api/live/*`），会话管理与交易操作。
- `settings_routes.py`：用户设置与凭证管理接口（`/api/settings/*`）。
- `walkforward_routes.py`：Walk-Forward 参数优化接口（`/api/walkforward/*`）。
- `websocket_routes.py`：WebSocket 实时推送接口，交易状态与系统事件广播。

## 非功能性要求（Non-Functional）
- 一致性：错误码/响应结构统一，便于前端与监控消费。
- 安全：在路由层做鉴权与权限检查，避免未授权访问。
- 可维护性：路由只做编排，不直接操作 DB 或外部 broker。

## 约定与规范
- 新路由文件命名为 `{feature}_routes.py`，对外暴露 `router`。
- 路由注册统一在 `backend/src/service/app.py` 完成。
- 接口变更需同步更新前端 `frontend/src/services/api.js` 及文档示例。

