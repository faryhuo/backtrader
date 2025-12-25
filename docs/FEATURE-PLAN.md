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
- [x] 回测结果深度分析（热图/Sharpe/分布/回撤/基准对比）：`backend/src/service/deep_analysis.py` + `backend/src/routes/backtest_routes.py` + `frontend/src/components/DeepAnalysis/`

### 策略编写与模板
- [x] 策略文件加载/保存/列表（带名称净化，防路径穿越）：`backend/src/service/backtest_engine.py`
- [x] 策略在线维护（Monaco Editor）：`frontend/src/pages/StrategyMaintain.jsx`
- [x] 策略模板库（分类/难度/详情/一键导入）：`backend/src/service/strategy_templates.py` + `backend/src/routes/api_routes.py`
- [x] 策略参数提取与覆盖（回测/组合回测复用）：`backend/src/routes/api_routes.py`（`/strategy/{name}/params`）
- [x] 策略版本管理（自动版本、历史、diff、回滚）：`backend/src/routes/strategy_routes.py` + `backend/src/db/storage/strategy_version.py` + `frontend/src/components/StrategyMaintain/`

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
- [x] 数据缓存管理（统计/预热/清理）：`backend/src/db/storage/data_cache.py` + `backend/src/routes/market_data_routes.py`
- [x] OHLCV 重采样（1m→5m→1h→1d）：`backend/src/db/storage/resampler.py`

#### [x] 任务中心（后台任务统一管理）
验收标准：
- 统一管理：回测 / 组合回测 / Walk-Forward / 深度分析等后台任务（状态、进度、耗时、失败原因）。
- 支持：取消/重试/并发上限；WebSocket 推送任务事件；前端提供任务列表与详情页。
- 任务输出可追踪到对应的历史记录（backtest/portfolio/walkforward id）。

#### [x] 统一错误结构与可观测性基础
验收标准：
- 后端统一错误响应结构（code/message/details/request_id），并对关键路径打点日志。
- 为回测/实盘/优化提供一致的 trace id，便于排障。

#### [x] 数据管理：预热/清理/重采样（已完成）
验收标准：
- 增加数据预热接口（批量拉取并入库），提供缓存命中率/最近更新时间。
- 支持 OHLCV 重采样（如 1m→5m→1h→1d），明确数据一致性策略。

#### [x] 报告中心（导出/分享）
验收标准：
- 支持对回测/组合回测/Walk-Forward/深度分析生成统一报告（HTML）。
- 支持下载与（可选）生成分享链接；报告包含关键指标、图表截图/矢量图、参数与环境信息（可复现）。
- 报告生成作为后台任务运行，可被缓存与再次查看。

实现：
- 后端：`backend/src/routes/report_routes.py` + `backend/src/service/report_generator.py`
- 前端：`frontend/src/pages/ReportCenter.jsx` + `frontend/src/pages/SharedReport.jsx`
- 分享链接：HMAC签名的URL（`backend/src/utils/share_token.py`），支持过期时间配置
- i18n：中英文双语报告（`backend/src/utils/report_i18n.py`）
- ECharts主题：统一图表样式（`backend/src/service/echarts_theme.py`）

---

## 部分完成（需要补齐）

### [~] Live 风控配置已存在，但缺少统一执行护栏
现状：配置层已经有 `risk_management`（如事件订阅里也包含 `risk_alert`）；前端也已有 Live 仪表盘与“风控”文案入口。

缺口：需要在 live 下单链路里形成“统一可插拔的风控护栏”，并把触发事件通过 WebSocket 回传给前端。

参考落点：`backend/src/utils/config_loader.py` + `backend/src/service/live_engine.py` + `frontend/src/pages/LiveTradingDashboard.jsx`

---

## Roadmap（按优先级）

### P0（建议先做：安全性与可运营性）

#### [~] 风控模块（Live 风控护栏）
目标：把“能跑”升级为“可安全上线”。

验收标准：
- 在 `paper`/`live` 模式下均可配置：最大仓位、单笔最大亏损、日内最大亏损、最大回撤阈值、交易时间窗口。
- 触发风控时：阻止下单/强平/停止会话（可配置），并通过 WebSocket 推送事件（建议 event type：`risk_alert`）。
- 前端在 `frontend/src/pages/LiveTradingDashboard.jsx` 展示风控状态与告警历史。

落点建议：`backend/src/service/risk_manager.py`（新增）+ `backend/src/service/live_engine.py` 集成；配置读取沿用 `backend/src/utils/config_loader.py`。


### P1（体验与分析能力增强）

#### [ ] 组合回测增强（Portfolio Enhancement）
验收标准：
- **组合净值曲线**：收集每个标的的 TimeReturn，按权重合成组合层面时序净值数据，前端可视化。
- **动态再平衡**：支持定期再平衡（月度/季度）或阈值触发再平衡（偏离目标权重超 X%）。
- **风险平价优化**：除 Markowitz 最大夏普外，提供风险平价权重、最小方差组合、等权重基准对比。
- **协方差稳健估计**：引入 Ledoit-Wolf 收缩估计或指数加权移动协方差。
- **动态策略参数**：允许不同标的使用不同策略参数。

落点：`backend/src/service/portfolio_backtest.py` + `frontend/src/pages/PortfolioBacktest.jsx`

#### [~] Backtrader 高级特性集成
验收标准：
- [x] **Sizer 可配置**：前端选择仓位管理策略（固定手数/百分比/全仓/风险控制/Kelly Criterion）。
- [x] **更多 Analyzers**：集成 Calmar、VWR 分析器（Sortino 不支持）。
- [x] **数据时间间隔选择**：支持 1d/1h/15m/5m/1m 时间粒度选择。
- [ ] **PyFolio 集成**：支持导出 PyFolio 兼容的分析数据（基础设施已就绪，待完善）。
- [ ] ~~Bracket Orders~~：已移出本期范围。

落点：`backend/src/service/worker/backtest_worker.py` + `frontend/src/components/RunStrategy/StrategyConfigForm.jsx`

#### [ ] 交易复盘中心（Trade Journal）
验收标准：
- 以“会话”为聚合：订单/成交/持仓变更/风控事件统一时间线，并可按标的/策略版本筛选。
- 支持导出（CSV/Excel）与备注（tag/笔记），便于复盘与分享。
- 与回测结果对齐：同一策略版本可对比 backtest vs live（关键指标与图表）。

#### [ ] 成本与滑点模型（Backtest/Live 一致）
验收标准：
- 可配置手续费/滑点模型（按交易所/标的/成交量阶梯），回测与实盘统一口径展示。
- 报告/深度分析中显示"含成本/不含成本"两套指标（至少净值曲线、Sharpe、最大回撤）。
- 支持 Backtrader 内置滑点模型（固定点数/百分比/成交量影响）。

#### [ ] 定时任务调度（回测/报告）
验收标准：
- 以 APScheduler 为主（单机先行），提供任务 CRUD、执行日志、失败重试策略。
- 支持：定时回测、定时 Walk-Forward、定时生成报告（先落库/文件，通知渠道后续扩展）。

#### [ ] 账户管理与资金曲线
验收标准：
- 支持多交易账户绑定（API Key/Secret 加密存储）；账户余额/持仓定时同步。
- 资金曲线历史记录与可视化；支持导出与对比（不同账户/不同时间段）。
- 与实盘会话关联：自动记录每笔交易对账户余额的影响。

#### [ ] 告警通知中心
验收标准：
- 支持多渠道通知：WebSocket（前端实时）、邮件、Webhook（飞书/钉钉/Slack）。
- 告警规则配置：风控触发、任务完成/失败、策略信号、账户异动。
- 告警历史记录与去重（防止重复发送）。

#### [ ] 策略市场与社区分享
验收标准：
- 用户可将策略发布为"公开/私有"；支持标签、描述、回测绩效展示。
- 其他用户可"fork"策略到自己的工作空间。
- 评论/点赞/收藏功能（可选）。

### P2（多租户与平台化）
- [ ] 多用户/团队协作：RBAC、工作空间隔离、策略分享/订阅。
- [ ] 监控告警：Prometheus/Grafana、关键指标告警、审计日志。
- [ ] 机器学习工作流：特征管道、训练/回测一体化、可解释性（SHAP）。
- [ ] 高频能力：Tick 级回测、订单簿、滑点与延迟建模。
- [ ] 数据源插件化：CSV/Parquet 导入、交易所 K 线、企业数据源（统一 schema + 数据质量校验）。
- [ ] 回放与调试：逐 bar 回放、断点/变量面板、关键事件时间线（订单/信号/风控）。
- [ ] 多交易所统一适配：CCXT 之外支持更多本地化交易所（如 A 股券商接口）。
- [ ] 回测预设与快速启动：常用回测配置模板（标的+策略+参数），一键复用。
- [ ] 移动端适配：响应式 UI 或 PWA，支持基础查看与告警推送。

---

## 技术债（持续清理）
- [~] 后端/前端关键路径补齐最小测试（pytest + 前端单测视情况）。
  - 已完成：核心 hooks 测试、storage 层测试、E2E 基础测试。
  - 待补齐：更多边界条件测试、性能测试。
- [ ] 性能基准：回测耗时、数据加载耗时、并发会话上限与压测脚本。
- [ ] 文档：API 示例、常见故障排查、生产部署 checklist（与 `SECURITY.md` 对齐）。
- [ ] 代码重构：减少循环依赖（已部分完成 types 层提取），统一错误处理。
- [ ] 日志标准化：统一日志格式、结构化日志输出、敏感信息脱敏。

*最后更新时间：2025-12-25*
