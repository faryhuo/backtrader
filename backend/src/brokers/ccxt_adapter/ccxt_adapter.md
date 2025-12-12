# ccxt_adapter 目录说明

CCXT 交易所适配器，将交易所行情/下单接口统一接入 Backtrader/内部引擎。

## 功能职责（Functional）
- `ccxt_store.py`：CCXT 连接与会话管理。
- `ccxt_data.py`：行情数据拉取/推送到 Backtrader DataFeed。
- `ccxt_broker.py`：订单、成交与持仓的映射与下单实现。

## 非功能性要求（Non-Functional）
- 安全：交易所 key/secret 只能从环境变量与 `config_loader.py` 读取。
- 可靠性：对网络超时、限频、交易所错误做分类并抛出明确异常。
- 性能：避免 import 阶段发起网络请求；连接懒加载并复用。

## 约定与规范
- CCXT/Backtrader 接口保持一致，避免自定义破坏性扩展。
- 新增交易所特性需提供最小回测/模拟下单验证。

