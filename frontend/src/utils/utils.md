# utils 目录说明

前端通用工具函数与辅助模块目录。

## 功能职责（Functional）
- `exportUtils.js`：数据导出工具（Excel/CSV 导出、图表截图等）。
- `formatters.js`：数据格式化工具（数字、日期、百分比等格式化）。
- 提供格式化、校验、计算、数据转换等可复用函数。
- 封装与业务无关的通用逻辑，供组件/Hook/服务层调用。

## 非功能性要求（Non-Functional）
- 纯函数优先：避免隐式副作用，保证输入输出可预测。
- 可测试性：关键工具函数需可单测覆盖常见/边界场景。

## 约定与规范
- 文件按功能聚合（如 `formatters.js`、`exportUtils.js`）。
- 避免在 utils 中引入 React 或页面/组件依赖。

## Recent Notes

- `strategyErrorFormatter.js` now centralizes strategy/backtest failure normalization so pages can render user-friendly error summaries and next-step suggestions without duplicating backend-message parsing.
