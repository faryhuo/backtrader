# LiveTrading 目录说明

实盘/模拟盘交易模块组件。

## 组件文件
- `LiveConfigForm.jsx`：实盘配置表单，设置交易所、交易对、策略参数等。
- `OrderLog.jsx`：订单日志组件，展示历史订单与成交记录。
- `PnLChart.jsx`：盈亏图表组件，可视化账户收益曲线。
- `PositionTable.jsx`：持仓表格组件，展示当前持仓与浮动盈亏。
- `SessionControls.jsx`：会话控制组件，启动/停止/重启交易会话。

## 功能职责（Functional）
- 展示实时行情、持仓、订单、交易日志。
- 提供启动/停止实盘、下单与风控交互。

## 非功能性要求（Non-Functional）
- 实时性：UI 需兼容 WebSocket 推送，避免卡顿。
- 安全：关键操作需二次确认，并清晰展示当前账户/环境（paper vs live）。

## 约定与规范
- 实盘相关按钮与状态必须通过后端返回的会话/权限决定可用性。

