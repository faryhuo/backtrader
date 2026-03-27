# OnboardingSetup 目录说明

首次安装引导页相关的复用组件目录。

## 功能职责（Functional）
- 承载 `OnboardingSetup.jsx` 中可独立维护的步骤组件与共享展示组件。
- 将大块步骤 UI 从页面中拆出，保留页面层只负责状态编排、校验与路由切换。

## 当前组件
- `SettingRow.jsx`：统一字段标题、提示与内容布局。
- `DataSourceSetupSection.jsx`：数据源启用、优先级排序与 EODHD Key 配置。
- `AISetupSection.jsx`：AI provider 配置与测试区域。
- `TradingSetupSection.jsx`：Binance `paper/live` 配置、guide 与测试区域。
- `ReviewSummary.jsx`：最终 review 摘要与前后改动展示。

## 非功能性要求（Non-Functional）
- 组件接口应保持语义清晰，优先通过 props 接收状态和事件处理函数。
- 展示逻辑可下沉到组件内，跨步骤的业务校验仍由页面层统一管理。

## 约定与规范
- 组件文件使用 PascalCase 命名并默认导出同名组件。
- 样式优先复用 `OnboardingSetup.css` 中的既有类名，避免无意义的样式分叉。

## Recent Notes

- The onboarding review summary now treats login state as a deployment-mode outcome instead of a separately configured security switch.
- `ReviewSummary.jsx` now builds the review from a recursive config diff so the final step shows all effective overrides instead of a hand-picked subset of fields.
- `AISetupSection.jsx` now captures the runtime model name for each enabled AI provider and passes that model into provider connection tests during onboarding.
- `DataSourceSetupSection.jsx` now mirrors the Settings page data-source workflow with source toggles, drag-to-reorder priority, and conditional EODHD key entry.
- `TradingSetupSection.jsx` now focuses only on Binance paper/live credentials and live enablement; default exchange, trade mode, and market are fixed by the wizard instead of being user-configurable.
