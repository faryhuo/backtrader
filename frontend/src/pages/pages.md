# pages 目录说明

页面级组件（路由视图）目录。

## 页面文件
- `Home.jsx`：首页/仪表盘，展示系统概览与快捷入口。
- `BacktestHistory.jsx`：回测历史页面，展示与管理历史回测结果。
- `Callback.jsx`：OAuth 回调页面，处理 Logto 认证回调。
- `DataSource.jsx`：数据源配置页面，管理交易品种与数据来源。
- `LiveTradingDashboard.jsx`：实盘交易仪表盘，实时监控交易会话与持仓。
  - 页面负责编排 live trading 的整体信息层级：会话概览与市场状态在顶部，关键运行指标与主图居中，持仓/错误/订单/策略日志收敛到右侧执行区。
- `RunStrategy.jsx`：策略运行页面，配置并执行回测任务。
- `Settings.jsx`：设置页面，管理用户偏好、交易所凭证与系统配置。
- `StrategyMaintain.jsx`：策略维护页面，编辑与管理策略代码。
- `WalkForward.jsx`：Walk-Forward 优化页面，参数优化与过拟合检测。

## 功能职责（Functional）
- 对应路由的顶层页面，负责组织子组件与页面级数据加载。
- 处理页面布局与导航的组合（与 `components/Layout` 配合）。

## 非功能性要求（Non-Functional）
- 清晰边界：页面负责"编排"，业务细节下沉到 `components/`/`hooks/`/`services/`。
- 性能：页面级请求需支持加载态、错误态与取消。

## 约定与规范
- 以功能域分文件/子目录，避免单文件过大。
- 路由变更需同步更新 `App.jsx` 或路由配置。

## Recent Notes

- `Settings.jsx` now presents a unified AI model provider section for OpenAI, MiniMax, Gemini, and Claude.
- `OnboardingSetup.jsx` now provides a dedicated first-run setup wizard for file-backed bootstrap configuration.
- `OnboardingSetup.jsx` now mirrors the unified AI provider model, removes `DATABASE_URL` / `VITE_API_BASE_URL` onboarding inputs, and keeps trading bootstrap limited to Binance with paper/live credentials shown together.
- `OnboardingSetup.jsx` now provides an official Binance API guide card directly above the Binance API key inputs, including creation, permission, and IP restriction guidance.
- `OnboardingSetup.jsx` review step now focuses on a grouped change summary so operators can confirm what settings changed, instead of reading backend file targets.
- `OnboardingSetup.jsx` now splits Binance trading setup into `paper` and `live` tabs, each with its own guide and mode-specific configuration block.
