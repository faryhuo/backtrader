# components 目录说明

组件根目录，包含通用组件与各业务模块组件。

## 子目录
- `Auth/`：认证相关组件（登录/登出按钮、受保护路由等）。
- `BacktestHistory/`：回测历史展示组件（列表、详情、图表等）。
- `DataSource/`：数据源配置组件（符号选择、时间范围等）。
- `Layout/`：应用布局组件（导航栏、侧边栏、页面框架）。
- `LiveTrading/`：实盘交易组件（交易面板、订单列表、持仓展示等）。
- `OnboardingSetup/`：首次安装引导页拆分组件（AI、Trading、Review 等步骤区域）。
- `RunStrategy/`：策略运行组件（参数配置、执行控制等）。
- `StrategyMaintain/`：策略维护组件（Monaco 编辑器、策略列表、模板选择等）。
- `WalkForward/`：Walk-Forward 优化组件（参数配置、结果展示等）。

## Recent Notes

- `OnboardingSetup/` now hosts the larger first-run wizard step components so `pages/OnboardingSetup.jsx` stays focused on orchestration and validation.
- `RunStrategy/StrategyConfigForm.jsx` now renders structured strategy failure alerts with actionable guidance instead of showing raw backend error strings directly.
- `RunStrategy/StrategyPlot.jsx` now shows both render-mode availability states and explains when the UI chart data or Backtrader image was not generated for a run.

## 功能职责（Functional）
- 提供跨页面复用的 UI/业务组件。
- 按功能域拆分子目录，每个子目录独立管理相关组件。

## 非功能性要求（Non-Functional）
- 可复用性：组件设计应关注 props API 的稳定与语义清晰。
- 可测试性：复杂逻辑组件应拆分为展示/容器或提取 Hook。
- 性能：对频繁渲染组件使用 `memo`/`useMemo`/`useCallback`。

## 约定与规范
- 组件文件与目录使用 PascalCase；导出默认组件与同名文件一致。
- 子目录内可包含 `index.js(x)` 作为聚合入口。
- 禁止在组件中直接访问 `.env` 或硬编码后端地址，统一走 `services/`。
