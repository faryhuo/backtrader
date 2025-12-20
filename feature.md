# Feature Plan（基于现状的功能规划）

本文件用于追踪“已经实现的能力”和“下一步要做什么”。避免把已上线功能重复写成 TODO。

## 状态标记
- `[x]` 已完成（可用）
- `[~]` 部分完成（已有基础，需要补齐）
- `[ ]` 规划中（未开始/待排期）

## 已上线功能（Done）

### 回测与结果管理
- [x] 单标的回测引擎（Backtrader + 指标/图表输出）：`backend/src/service/backtest_engine.py`
- [x] 回测历史持久化、筛选/排序、详情/删除：`backend/src/routes/api_routes.py` + `backend/src/db/backtest_storage.py`
- [x] 回测 AI 分析结果可回写保存：`backend/src/routes/api_routes.py`（`/backtest/history/*/ai-analysis`）

### 策略编写与模板
- [x] 策略文件加载/保存/列表（带名称净化，防路径穿越）：`backend/src/service/backtest_engine.py`
- [x] 策略在线维护（Monaco Editor）：`frontend/src/pages/StrategyMaintain.jsx`
- [x] 策略模板库（分类/难度/详情/一键导入）：`backend/src/service/strategy_templates.py` + `backend/src/routes/api_routes.py`
- [x] 策略参数提取与覆盖（回测/组合回测复用）：`backend/src/routes/api_routes.py`（`/strategy/{name}/params`）

### Walk-Forward 参数优化与可视化
- [x] 后台任务式 Walk-Forward 优化 + 结果持久化：`backend/src/routes/walkforward_routes.py` + `backend/src/db/walkforward_storage.py`
- [x] 过拟合检测、参数敏感度、2D 热力图数据：`backend/src/service/parameter_analysis.py`
- [x] 前端热力图可视化（ECharts）：`frontend/src/components/WalkForward/ParameterHeatmap.jsx`

### 组合回测（Portfolio）
- [x] 多标的组合回测（并行回测、相关性矩阵、Markowitz 建议、组合图）：`backend/src/service/portfolio_backtest.py`
- [x] 组合回测历史/详情/删除：`backend/src/routes/portfolio_routes.py` + `backend/src/db/portfolio_storage.py`
- [x] 前端组合回测页面：`frontend/src/pages/PortfolioBacktest.jsx`

### 实盘/模拟交易与实时推送
- [x] 实盘/模拟交易会话（启动/停止/状态/列表/订单/健康检查）：`backend/src/routes/live_routes.py`
- [x] WebSocket 实时推送（基于 `ws_token` 的会话级鉴权）：`backend/src/routes/websocket_routes.py`
- [x] 会话/订单/持仓持久化模型：`backend/src/db/models.py`

### 设置、凭证与安全
- [x] 用户设置（模型选择、提示词模板）持久化：`backend/src/routes/settings_routes.py` + `backend/src/db/settings_storage.py`
- [x] 凭证托管与测试（OpenAI/代理/CCXT/Logto），敏感字段加密存储（Fernet）：`backend/src/db/settings_storage.py`
- [x] 策略沙箱执行（支持 subprocess 隔离 + 软回退模式）：`backend/src/service/isolated_sandbox.py` + `backend/src/service/backtest_engine.py`
- [x] 可选的 Logto JWT 鉴权（可开关）：`backend/src/utils/auth.py` + `backend/src/routes/settings_routes.py`

### 数据源与缓存
- [x] 市场数据与标的元数据缓存到数据库（减少重复拉取）：`backend/src/db/datasource.py` + `backend/src/db/models.py`

---

## 部分完成（需要补齐）

### [~] 策略版本管理（Versioning）
现状：已有 `strategy_versions` 表模型：`backend/src/db/models.py`（`StrategyVersionModel`）。

缺口：缺少写入版本的存储层、API、前端时间线/对比/回滚，以及在保存策略时自动落库。

### [~] 数据管理与预热
现状：数据会被自动缓存到 DB；但缺少“可视化的缓存状态/清理/预热/重采样”的管理能力。

缺口：需要补齐管理端点与前端入口（例如 DataSource 页补一个缓存面板）。

---

## Roadmap（按优先级）

### P0（建议先做：安全性与可运营性）

#### [ ] 风控模块（Live 风控护栏）
目标：把“能跑”升级为“可安全上线”。

验收标准：
- 在 `paper`/`live` 模式下均可配置：最大仓位、单笔最大亏损、日内最大亏损、最大回撤阈值、交易时间窗口。
- 触发风控时：阻止下单/强平/停止会话（可配置），并通过 WebSocket 推送事件。
- 前端在 `frontend/src/pages/LiveTradingDashboard.jsx` 展示风控状态与告警历史。

落点建议：`backend/src/service/risk_manager.py`（新增）+ `backend/src/service/live_engine.py` 集成。

#### [ ] 策略版本管理（完整闭环）
验收标准：
- 保存策略时自动生成版本；支持版本列表、diff、回滚；支持可选 commit message。
- API：`/api/strategy/{name}/versions`（list/get/diff/rollback）。
- 前端：策略维护页增加“版本”入口，支持 diff 视图。

#### [ ] 统一错误结构与可观测性基础
验收标准：
- 后端统一错误响应结构（code/message/details/request_id），并对关键路径打点日志。
- 为回测/实盘/优化提供一致的 trace id，便于排障。

### P1（体验与分析能力增强）

#### [ ] 回测结果深度分析（含基准对比）
验收标准：
- 支持：月度收益热图、滚动 Sharpe、收益分布/回撤分布、最大连续亏损、与基准对比（可选 SPY/沪深300 等）。
- 前端图表统一在组件层封装（避免页面堆图表逻辑）。

#### [ ] 数据管理：预热/清理/重采样
验收标准：
- 增加数据预热接口（批量拉取并入库），提供缓存命中率/最近更新时间。
- 支持 OHLCV 重采样（如 1m→5m→1h→1d），明确数据一致性策略。

#### [ ] 定时任务调度（回测/报告）
验收标准：
- 以 APScheduler 为主（单机先行），提供任务 CRUD、执行日志、失败重试策略。
- 支持：定时回测、定时 Walk-Forward、定时生成报告（先落库/文件，通知渠道后续扩展）。

### P2（多租户与平台化）
- [ ] 多用户/团队协作：RBAC、工作空间隔离、策略分享/订阅。
- [ ] 监控告警：Prometheus/Grafana、关键指标告警、审计日志。
- [ ] 机器学习工作流：特征管道、训练/回测一体化、可解释性（SHAP）。
- [ ] 高频能力：Tick 级回测、订单簿、滑点与延迟建模。

---

## 技术债（持续清理）
- [ ] 后端/前端关键路径补齐最小测试（pytest + 前端单测视情况）。
- [ ] 性能基准：回测耗时、数据加载耗时、并发会话上限与压测脚本。
- [ ] 文档：API 示例、常见故障排查、生产部署 checklist（与 `SECURITY.md` 对齐）。

*最后更新时间：2025-12-20*
