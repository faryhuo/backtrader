# brokers 目录说明

交易所 / 券商适配层，负责把不同外部交易接口整理成系统内部可消费的统一能力。

## 子目录
- `binance_adapter/`: Binance 现货适配器。

## Binance 适配器分层
`binance_adapter/` 保持三层运行时模块，各自只做一件事：
- `binance_store.py`: 连接层。负责 Binance REST / WebSocket 访问、paper trading 状态、订单与行情原始读写。
- `binance_data.py`: 数据层。负责把 Store 提供的 OHLCV 数据转换成 Backtrader `DataBase` 数据流，并处理 backfill、去重、未收盘 K 线过滤。
- `binance_broker.py`: 交易层。负责把 Backtrader `Order` 映射为交易所订单，维护持仓、现金、成交回报和事件通知。

补充约束：
- `__init__.py` 只做包入口导出，不再承载共享常量或业务逻辑。
- `common.py` 只存放纯函数和共享常量，例如 symbol / timeframe 转换，不参与连接、行情或交易状态管理。
- 任何新增 Binance 能力，优先判断属于连接层、数据层还是交易层，禁止跨层复制相同转换逻辑。

## 功能职责
- 将外部交易接口适配为 Backtrader / 系统服务可直接调用的统一接口。
- 提供稳定的 `Store + Data + Broker` 组合，供 `service/live_engine.py` 和 worker 使用。
- 屏蔽交易所细节差异，例如 symbol 格式、K 线周期、订单状态、paper trading 模拟。

## 非功能要求
- 可靠性：网络异常、交易所异常、WebSocket 中断必须可定位，日志要区分连接层、数据层、交易层。
- 可维护性：共享规则集中在纯工具模块，避免在 `__init__.py`、`store`、`data`、`broker` 中重复定义。
- 安全性：敏感凭证只能通过配置和环境变量注入，模块 import 阶段不得主动发起网络连接。
- 性能：连接对象延迟初始化并尽量复用，避免重复创建客户端和重复拉取相同时间窗口数据。

## 约定与规范
- 适配器目录对外暴露清晰入口，外部调用默认从包级别导入。
- 共享工具必须保持无副作用，便于单测和后续扩展到其他交易所适配器。
- 如果后续新增交易所，优先复用这一分层方式：连接层、数据层、交易层，再补一个轻量共享模块承载纯转换逻辑。
