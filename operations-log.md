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
