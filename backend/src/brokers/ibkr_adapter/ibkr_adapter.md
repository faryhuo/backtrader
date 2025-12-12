# ibkr_adapter 目录说明

- 作用：封装 Backtrader 自带的 `IBStore`，提供与 CCXT 适配器一致的 start/stop/get_broker/get_data 接口，便于在 `live_engine` 内按交易所配置自动选择 IBKR 或 CCXT。
- 依赖：本地 IB Gateway/TWS（推荐 paper 端口 7497，实盘 7496）与 IB API；环境变量可覆盖连接信息：
  - `IBKR_PAPER_HOST` / `IBKR_LIVE_HOST`（默认 127.0.0.1）
  - `IBKR_PAPER_PORT` / `IBKR_LIVE_PORT`（默认 7497/7496）
  - `IBKR_PAPER_CLIENT_ID` / `IBKR_LIVE_CLIENT_ID`（默认 1）
  - `IBKR_PAPER_ACCOUNT` / `IBKR_LIVE_ACCOUNT`（可选，指定账户号）
- 符号格式：`get_data` 直接接受 IB 合约字符串（如 `AAPL-STK-SMART-USD`、`EUR.USD-CASH-IDEALPRO`），确保外部调用使用合法合约。
- 时间粒度：支持 `1m/5m/15m/30m/1h/4h/1d` 映射到 Backtrader TimeFrame。
- 开发约束：保持懒加载、避免在导入阶段发起网络连接；异常使用 `IBKRStoreError` 抛出，由上层统一处理。
