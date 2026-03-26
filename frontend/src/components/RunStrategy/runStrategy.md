# RunStrategy 目录说明

策略运行与回测启动模块组件。

## 组件文件
- `AIInsight.jsx`：AI 洞察组件，展示 AI 对回测结果的分析与建议。
- `PerformanceOverview.jsx`：绩效概览组件，展示关键回测指标（夏普比率、最大回撤等）。
- `StrategyConfigForm.jsx`：策略配置表单，设置回测参数（时间范围、初始资金、手续费等）。
- `StrategyPlot.jsx`：策略图表组件，展示回测收益曲线与买卖点标记。
- `TradeLog.jsx`：交易日志组件，展示回测中的所有交易记录。

## 功能职责（Functional）
- 策略参数配置、回测/运行启动、结果概览与图表展示。
- 支持加载/保存策略配置与模板。

## 非功能性要求（Non-Functional）
- 易用性：表单与参数需有默认值与校验提示。
- 性能：图表绘制应分层/节流，避免阻塞交互。

## 约定与规范
- 参数 schema 与后端策略执行接口保持一致。
## Recent Notes

- `StrategyPlot.jsx` should prefer structured backend `chart_data` over static images, using `plot_url` only as a compatibility fallback.
- `StrategyPlot.jsx` now routes chart summary text, OHLC tooltip labels, broker legend labels, and image alt text through i18n keys in `history.json`.
