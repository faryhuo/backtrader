# brokers 目录说明

交易/券商适配层目录，用于将不同交易所或券商的行情与下单接口统一到系统内部抽象。

## 子目录
- `ccxt_adapter/`：CCXT 加密货币交易所适配器（Binance、OKX、Bybit 等）。
- `ibkr_adapter/`：Interactive Brokers 传统证券适配器。

## 功能职责（Functional）
- 适配外部交易接口到 Backtrader/内部引擎可消费的统一接口。
- 提供 `get_broker`、`get_data`、`start/stop` 等一致的调用面，供 `service/live_engine.py` 使用。
- 管理不同 broker 的配置解析与能力差异（时间粒度、符号格式、手续费等）。

## 非功能性要求（Non-Functional）
- 可靠性：网络/交易所异常要有清晰的错误分类，支持上层重试与降级。
- 安全：敏感凭证仅通过 `config/` 与环境变量加载。
- 性能：避免在 import 阶段发起网络连接；连接应懒加载并可复用。

## 约定与规范
- 子目录以适配器名称命名，内部提供清晰的入口文件与异常类型。
- 适配器对外暴露的接口需与现有 CCXT/IBKR 适配器保持一致。

