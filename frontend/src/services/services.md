# services 目录说明

前端服务层目录，负责与后端 API、WebSocket 及外部 AI 服务交互，对上层组件提供稳定、可复用的调用接口。

## 功能职责（Functional）
- `api.js`：API 基础配置与通用请求封装（API_URL、鉴权 token 管理、`buildRequest`/`parseResponse`、标准 CRUD 与交易相关调用）。
- `aiAnalysis.js`：AI 分析服务封装（获取 AI 设置/模型、策略全量分析、代码分析/重写、多模态图表分析等工作流）。
- `websocket.js`：实时数据 WebSocket 连接管理、订阅与消息分发。

## 非功能性要求（Non-Functional）
- 可靠性：所有对外接口需统一错误格式与异常处理，避免组件层各自 try/catch。
- 安全：不在此目录硬编码密钥；敏感参数仅来自环境变量或后端下发。
- 可维护性：接口命名语义化，避免直接暴露后端细节；变更需做兼容层或同步更新调用方。
- 可测试性：纯解析/转换函数应易于单测，避免与 UI 耦合。

## 约定与规范
- 服务方法按业务域分组导出，避免“巨型 api 文件”。
- WebSocket 事件名与 payload schema 必须与后端 `backend/src/routes/websocket_routes.py` 约定一致。
- 新增接口需同步更新类型/注释与对应页面/组件使用方式。
