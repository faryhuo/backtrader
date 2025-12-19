# db 目录说明

持久化与数据模型目录，基于 SQLAlchemy/SQLite 管理交易会话、订单、持仓等数据。

## 功能职责（Functional）
- `models.py`：定义会话/订单/持仓/凭证等数据模型（TradingSession, Order, Position, UserCredential 等）。
- `backtest_storage.py`：回测历史存取，支持结果持久化与查询。
- `datasource.py`：数据源管理与市场数据获取（yfinance/CCXT）。
- `session_storage.py`：实盘/模拟盘会话 CRUD 与状态查询。
- `settings_storage.py`：用户设置与凭证存储，支持加密凭证管理。
- `walkforward_storage.py`：Walk-Forward 优化结果持久化与查询。

## 非功能性要求（Non-Functional）
- 数据安全：破坏性变更前需备份；测试使用内存库或临时 SQLite；凭证需加密存储。
- 兼容性：字段与表结构变更需考虑向后兼容或提供迁移脚本。
- 可维护性：模型与交易域语义保持一致，避免"万能表"。

## 约定与规范
- DB 层不写业务流程，只负责数据定义与访问。
- 跨模块引用模型需通过明确接口，避免循环依赖。
- 敏感数据（API Key/Secret）必须使用 `utils/encryption.py` 加密后存储。

