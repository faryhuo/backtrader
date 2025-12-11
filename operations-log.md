## 2025-11-12

- 修复 CCXTData 初始化：透传 **kwargs 给 Backtrader 基类，确保 timeframe/backfill 等参数不被丢弃。
- 记录上下文扫描至 `.codex/context-scan.json`。
- 暂未执行自动化测试（项目未提供测试入口）。如需，后续可添加针对 timeframe 参数的单测或冒烟脚本。

## 2025-12-11

- 复现 ccxt 导入时报 pycares 无 ares_query_a_result，定位为 pycares 5.0.0 与 aiodns 3.6.0 的兼容性问题。
- 在 backend/requirements.txt pin aiodns>=3.0,<4.0 与 pycares>=4.3,<5.0，并在 README_LIVE_TRADING.md 补充安装故障排查说明。
- 未运行自动化测试：沙箱只读且当前环境仍是 pycares 5.0.0，无法降级验证；需在可写环境重新安装依赖后再跑冒烟/单测。
- 优化 backend/src/strategy/strategy.md，明确目录用途、人机协作边界、命名规范与变更流程，避免误改用户策略。
- 将路由目录自 backend/src/service/routes 迁移至 backend/src/routes，更新 FastAPI 入口导入路径；为 brokers/config/db/service/routes/utils 及 ccxt_adapter 创建 {folder_name}.md 说明，补充使用规范与协作边界。
- 修复 live 交易运行时报 Backtrader `NotImplementedError`：为 CCXTBroker 添加 `getcash`/`getvalue` 兼容方法；在 live_engine 过滤 protobuf gencode/runtime 版本告警，避免日志刷屏。运行 `python -m pytest auto_test -q` 全部通过，剩余第三方迁移 warnings 待后续升级处理。
- 升级到高版本 `aiodns>=3.6.0`/`pycares>=5.0.0`，新增 `src/utils/dns_compat.py` 兼容层，在 CCXT 适配器导入前对 pycares Channel 与缺失的 `ares_*` 类进行补丁，确保 aiodns 在 pycares 5.x 下可导入与解析；更新 README_LIVE_TRADING.md 说明并重新跑 `pytest auto_test -q` 通过。
