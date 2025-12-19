# ibkr_adapter 目录说明

IBKR 适配器，对 Backtrader 自带 `IBStore` 进行封装，提供与 CCXT 适配器一致的调用接口。

## 功能职责（Functional）
- `ibkr_store.py`：IBKR 连接管理与接口封装，提供 `get_broker`、`get_data` 统一接口。
- 在 `service/live_engine.py` 中可按 broker 配置自动选择 IBKR 或 CCXT。
- `get_data` 接受 IB 合约字符串（如 `AAPL-STK-SMART-USD`）。
- 支持常用时间粒度映射到 Backtrader TimeFrame。

## 非功能性要求（Non-Functional）
- 可靠性：连接/订阅失败需抛出 `IBKRStoreError`，由上层统一处理。
- 安全：连接信息来自环境变量（如 `IBKR_*`），不得硬编码账号。
- 性能：保持懒加载，避免在 import 阶段建立 TWS/Gateway 连接。

## 约定与规范
- 依赖本地 IB Gateway/TWS（paper 默认端口 4002，live 默认端口 4001）。
- 新增合约/时间粒度支持需补充最小验证用例。

