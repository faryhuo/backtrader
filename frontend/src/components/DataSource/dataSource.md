# DataSource 目录说明

数据源管理模块组件。

## 组件文件
- `CandleStickChart.jsx`：K 线图组件，基于 Lightweight Charts 展示 OHLCV 数据。
- `ChartToolbar.jsx`：图表工具栏，支持时间周期切换、指标添加等。
- `DataSourceConfigForm.jsx`：数据源配置表单，设置数据源类型与参数。
- `IndicatorsPanel.jsx`：指标面板组件，添加/移除技术指标。
- `QuickPicks.jsx`：快速选择组件，常用交易品种快捷入口。
- `TickerInfoPanel.jsx`：品种信息面板，展示当前选中品种的详细信息与行情。

## 功能职责（Functional）
- 管理行情/数据源的配置、连接测试、数据预览。
- 提供数据源选择控件给策略/回测使用。

## 非功能性要求（Non-Functional）
- 可靠性：对网络/权限错误提供可恢复提示。
- 安全：不在 UI 中暴露敏感连接信息。

## 约定与规范
- 仅通过 `services/` 调用后端数据源相关接口。

