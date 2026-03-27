# frontend/src 目录说明

本目录是前端应用的源码根目录，基于 React + Vite 组织 UI、状态、路由、国际化与服务调用。

## 功能职责（Functional）
- 入口与应用壳：`main.jsx` 挂载应用，`App.jsx` 组织全局布局与路由。
- 业务视图：`pages/` 提供页面级路由视图。
- 业务组件：`components/` 提供可复用的业务/通用组件。
- 数据与服务：`services/` 封装与后端/第三方的 API、WebSocket、AI 分析等交互。
- 状态与上下文：`providers/` 提供 Context/状态容器与全局依赖注入。
- 配置与常量：`config/` 聚合运行时配置、常量、枚举。
- 工具与 Hook：`utils/`、`hooks/` 提供通用工具函数与自定义 Hook。
- 资源与国际化：`assets/` 静态资源；`locales/` 多语言文案与 `i18n.js` 配置。

## 非功能性要求（Non-Functional）
- 可维护性：按“页面/组件/服务/工具”分层，避免跨层循环依赖。
- 可测试性：纯工具函数与 Hook 需具备可单测结构；复杂组件建议拆分为可测小单元。
- 性能：避免无必要的全局重渲染；大列表/图表优先做虚拟化与 memo 化。
- 可用性：交互与文案需支持多语言与无障碍（键盘、ARIA）。
- 安全：不在前端硬编码密钥；敏感信息只通过后端下发的短期令牌/会话获取。

## 约定与规范
- 目录内组件/页面使用 PascalCase 文件夹与 `.jsx`/`.tsx` 文件名；工具/服务使用 camelCase。
- 业务组件尽量就近放置在对应 feature 子目录下，避免 `components/` 变成“杂物间”。
- 服务调用统一走 `services/`，不要在组件内直接写 fetch/axios。
- 新增环境变量需同步更新 `frontend/.env` 示例及对应文档。

## Recent Notes

- `App.jsx` now checks `GET /api/setup/wizard` before rendering normal app routes. When `status.is_ready` is `false`, first-entry traffic is redirected to `/onboarding`; once setup is ready, normal routing resumes without forcing the wizard.
