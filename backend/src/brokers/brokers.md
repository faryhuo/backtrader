# brokers 目录说明

- 作用：封装与交易所/行情源的适配层，目前集中在 `ccxt_adapter`，为 Backtrader 提供 Store/Data/Broker。
- 责任边界：不直接依赖 FastAPI/路由；初始化时避免副作用（避免导入即发请求），异常向上抛出由上层处理。
- 结构命名：子目录按适配器命名，公共基类/工具可放同级；新适配器遵循 CCXT/Backtrader 字段命名（symbol/timeframe/commission 等）。
- 协作与测试：新增/修改时补最小化回测或模拟测试，记录依赖版本与必需配置；涉及密钥的配置放 `.env` 或独立配置文件，禁止提交到仓库。
