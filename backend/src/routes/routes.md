# routes 目录说明

FastAPI 路由与接口层目录，集中维护 HTTP/WebSocket API。

## 功能职责（Functional）
- 定义各业务域路由：策略、回测、数据源、实盘、AI、WebSocket 等。
- 完成请求校验、参数解析、调用服务层并返回统一响应。
- 管理静态资源/前端挂载（如有）。

## 非功能性要求（Non-Functional）
- 一致性：错误码/响应结构统一，便于前端与监控消费。
- 安全：在路由层做鉴权与权限检查，避免未授权访问。
- 可维护性：路由只做编排，不直接操作 DB 或外部 broker。

## 约定与规范
- 新路由文件命名为 `{feature}_routes.py`，对外暴露 `router`。
- 路由注册统一在 `backend/src/service/app.py` 完成。
- 接口变更需同步更新前端 `frontend/src/services/api.js` 及文档示例。

