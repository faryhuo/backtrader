# components 目录说明

组件根目录，包含通用组件与各业务模块组件。

## 功能职责（Functional）
- 提供跨页面复用的 UI/业务组件。
- 按功能域拆分子目录（如 `RunStrategy/`、`LiveTrading/`）。

## 非功能性要求（Non-Functional）
- 可复用性：组件设计应关注 props API 的稳定与语义清晰。
- 可测试性：复杂逻辑组件应拆分为展示/容器或提取 Hook。
- 性能：对频繁渲染组件使用 `memo`/`useMemo`/`useCallback`。

## 约定与规范
- 组件文件与目录使用 PascalCase；导出默认组件与同名文件一致。
- 子目录内可包含 `index.js(x)` 作为聚合入口。
- 禁止在组件中直接访问 `.env` 或硬编码后端地址，统一走 `services/`。

