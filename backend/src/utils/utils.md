# utils 目录说明

后端通用工具函数与辅助模块目录。

## 功能职责（Functional）
- `auth.py`：JWT 鉴权与用户验证（Logto 集成）。
- `config_loader.py`：Broker 配置加载与解析（从 `broker_config.json` 与环境变量）。
- `credential_validator.py`：交易所凭证格式校验与连接测试。
- `encryption.py`：敏感数据加密/解密工具（Fernet 对称加密）。
- `exception_handlers.py`：统一异常处理器注册与错误响应结构（供 FastAPI 全局使用）。

## 非功能性要求（Non-Functional）
- 纯函数优先：避免隐藏全局状态与副作用。
- 可测试性：关键工具函数应覆盖正常/异常路径。
- 安全：加密密钥必须从环境变量获取，不得硬编码。

## 约定与规范
- 按功能域拆分文件，接口保持小而清晰。
- 不在 utils 中依赖具体业务模块，防止循环引用。

## Recent Notes

- `credential_validator.py` now validates Binance credentials against the production endpoint by default, even for the `paper` credential slot. Testnet validation is now opt-in.
- `config_loader.py` now backfills default broker notification settings when older `broker_config.json` files omit the `notifications` block.

