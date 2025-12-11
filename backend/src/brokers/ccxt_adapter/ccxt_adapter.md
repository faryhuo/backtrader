# ccxt_adapter 目录说明

- 作用：通过 CCXT 将交易所行情与下单对接到 Backtrader，包括 `ccxt_store.py`（连接与会话管理）、`ccxt_data.py`（数据馈送）、`ccxt_broker.py`（下单/持仓映射）。
- 配置来源：交易所与账号参数来自 `config_loader.py` 读取的配置/`.env`，不得写死密钥；时间框架、手续费等与策略/路由参数保持一致。
- 开发约定：遵循 CCXT/Backtrader 接口，避免在 import 阶段发起网络请求；异常用清晰的错误信息向上抛出，由服务层决定重试/失败策略。
- 测试建议：优先使用沙箱或 paper mode 账号；新增功能需跑最小化回测/模拟下单，确认时区、费率、精度、节流（rate limit）行为符合预期。
