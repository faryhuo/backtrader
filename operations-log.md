## 2025-11-12

- 修复 CCXTData 初始化：透传 **kwargs 至 Backtrader 基类，确保 timeframe/backfill 等参数不丢失。
- 记录上下文扫描至 `.codex/context-scan.json`。
- 暂未执行自动化测试（缺少入口）。

## 2025-12-11

- 复现 ccxt 导入时报 pycares 无 ares_query_a_result，定位为 pycares 5.0.0 与 aiodns 3.6.0 兼容性问题；在 requirements pin aiodns/pycares 低版本并补充 README 故障排查。
- 路由目录从 backend/src/service/routes 迁移到 backend/src/routes，补充各目录 {folder_name}.md 协作说明；策略目录文档完善。
- CCXTBroker 补充 `getcash`/`getvalue` 兼容方法；live_engine 过滤 protobuf 版本警告；新增 DNS 兼容层适配 aiodns 3.x + pycares 5.x。
- 运行 `python -m pytest auto_test -q` 通过，余第三方迁移 warning 待后续处理。

## 2025-12-12

- 新增 IBKR 适配器（backend/src/brokers/ibkr_adapter/*），包装 Backtrader IBStore，支持 IBKR_{MODE}_HOST/PORT/CLIENT_ID/ACCOUNT 环境变量；requirements 增加 ibapi。
- live_engine 通过 `_build_components` 按配置 adapter 自动选择 CCXT/IBKR，策略代码无感切换纸盘/实盘；broker_config.json/template 增加 adapter 字段与 IBKR 示例；live_routes ExchangeInfo 输出 adapter，config_loader 校验 adapter。
- 运行 `python -m pytest auto_test -q` 9/9 通过，仅剩第三方弃用 warnings。
