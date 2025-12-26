# Feature Plan（基于现状的功能规划）

本文件用于追踪"已经实现的能力"和"下一步要做什么"。避免把已上线功能重复写成 TODO。

## 状态标记
- `[x]` 已完成（可用）
- `[~]` 部分完成（已有基础，需要补齐）
- `[ ]` 规划中（未开始/待排期）

---

## 一、已上线功能（Done）

### 1.1 回测与结果管理
- [x] 单标的回测引擎（Backtrader + 指标/图表输出）
- [x] 回测历史持久化、筛选/排序、详情/删除
- [x] 回测 AI 分析结果可回写保存
- [x] 回测结果深度分析（热图/Sharpe/分布/回撤/基准对比）
- [x] 数据时间间隔选择：支持 1d/1h/15m/5m/1m 时间粒度

### 1.2 策略编写与模板
- [x] 策略文件加载/保存/列表（带名称净化，防路径穿越）
- [x] 策略在线维护（Monaco Editor）
- [x] 策略模板库（分类/难度/详情/一键导入）
- [x] 策略参数提取与覆盖（回测/组合回测复用）
- [x] 策略版本管理（自动版本、历史、diff、回滚）

### 1.3 Walk-Forward 参数优化与可视化
- [x] 后台任务式 Walk-Forward 优化 + 结果持久化
- [x] 过拟合检测、参数敏感度、2D 热力图数据
- [x] 前端热力图可视化（ECharts）

### 1.4 组合回测（Portfolio）
- [x] 多标的组合回测（并行回测、相关性矩阵、Markowitz 建议、组合图）
- [x] 组合回测历史/详情/删除
- [x] 前端组合回测页面

### 1.5 实盘/模拟交易与实时推送
- [x] 实盘/模拟交易会话（启动/停止/状态/列表/订单/健康检查）
- [x] WebSocket 实时推送（基于 `ws_token` 的会话级鉴权）
- [x] 会话/订单/持仓持久化模型
- [x] CCXT 适配器（支持 Binance, OKX, Bybit 等）
- [x] IBKR 适配器（Interactive Brokers）

### 1.6 设置、凭证与安全
- [x] 用户设置（模型选择、提示词模板）持久化
- [x] 凭证托管与测试（OpenAI/代理/CCXT/Logto），敏感字段加密存储（Fernet）
- [x] 策略沙箱执行（支持 subprocess 隔离 + 软回退模式）
- [x] 可选的 Logto JWT 鉴权（可开关）

### 1.7 数据源与缓存
- [x] 市场数据与标的元数据缓存到数据库
- [x] 数据缓存管理（统计/预热/清理）
- [x] OHLCV 重采样（1m→5m→1h→1d）

### 1.8 平台基础设施
- [x] 任务中心（后台任务统一管理：回测/组合回测/Walk-Forward/深度分析）
- [x] 统一错误结构与可观测性基础（code/message/details/request_id）
- [x] 报告中心（HTML报告生成/下载/分享链接）

### 1.9 Backtrader 高级特性
- [x] **Sizer 可配置**：固定手数/百分比/全仓/风险控制/Kelly Criterion
- [x] **Analyzers 集成**：Sharpe, DrawDown, Returns, AnnualReturn, SQN, TradeAnalyzer, Calmar, VWR
- [x] **PyFolio 集成**：ZIP 导出、QuantStats 在线报告、PyFolio 风格指标
- [x] **订单类型**：Market, Limit, Stop, StopLimit（CCXT adapter 支持）

---

## 二、部分完成（需要补齐）

### [~] Live 风控配置
**现状**：配置层已有 `risk_management`，前端有 Live 仪表盘与"风控"入口。

**缺口**：需要在 live 下单链路里形成"统一可插拔的风控护栏"，触发事件通过 WebSocket 回传。

---

## 三、Roadmap（按优先级）

### P0：安全性与可运营性

#### [ ] 风控模块（Live 风控护栏）
**目标**：把"能跑"升级为"可安全上线"。

**验收标准**：
- 在 `paper`/`live` 模式下可配置：最大仓位、单笔最大亏损、日内最大亏损、最大回撤阈值、交易时间窗口
- 触发风控时：阻止下单/强平/停止会话（可配置），WebSocket 推送 `risk_alert` 事件
- 前端展示风控状态与告警历史

**落点**：`backend/src/service/risk_manager.py`（新增）+ `live_engine.py` 集成

---

### P1：体验与分析能力增强

#### [ ] 高级订单类型支持
**验收标准**：
- **StopTrail（尾随止损）**：支持 `trailamount`（固定金额）和 `trailpercent`（百分比）
- **StopTrailLimit**：尾随止损触发后以限价执行
- **Bracket Orders（括号单）**：同时设置止损和止盈，父单执行后子单激活
- 前端策略配置增加"高级订单"面板
- 策略模板库增加使用高级订单的示例

**落点**：`backend/src/brokers/ccxt_adapter/ccxt_broker.py` + 策略模板

#### [ ] 多时间框架混合回测（Multi-Timeframe）
**验收标准**：
- 同一策略可同时接入多个 timeframe 数据（如 1h + 1d）
- 前端 TimeFrame 支持多选
- 策略可通过 `self.data0`, `self.data1` 访问不同周期数据
- 文档说明多 timeframe 策略编写方法

**落点**：`frontend/src/components/RunStrategy/StrategyConfigForm.jsx` + 策略模板

#### [ ] 成本与滑点模型增强
**验收标准**：
- 可配置手续费模型：固定值/百分比/阶梯（按成交量）
- 多品种不同手续费率（组合回测中）
- 滑点模型：固定点数/百分比/成交量影响
- 报告显示"含成本/不含成本"两套指标
- 支持期货保证金模型（可选）

**落点**：`backend/src/service/backtest_engine.py` + 前端配置表单

#### [ ] 组合回测增强（Portfolio Enhancement）
**验收标准**：
- **组合净值曲线**：按权重合成组合层面时序净值，前端可视化
- **动态再平衡**：定期再平衡（月度/季度）或阈值触发再平衡
- **风险平价优化**：除 Markowitz 外提供风险平价、最小方差、等权重对比
- **协方差稳健估计**：Ledoit-Wolf 收缩估计或指数加权移动协方差
- **动态策略参数**：不同标的可使用不同策略参数

**落点**：`backend/src/service/portfolio_backtest.py` + 前端页面

#### [ ] 数据过滤器（Filters）
**验收标准**：
- **SessionFilter**：过滤盘外交易数据，支持交易时段配置
- **Replay 模式**：重放低频数据模拟高频 bar 形成过程（更真实回测）
- **HeikinAshi**：平均 K 线转换
- 前端数据配置增加"数据预处理"选项

**落点**：数据加载模块 + 前端配置

#### [ ] 交易复盘中心（Trade Journal）
**验收标准**：
- 以"会话"为聚合：订单/成交/持仓变更/风控事件统一时间线
- 支持按标的/策略版本筛选
- 支持导出（CSV/Excel）与备注（tag/笔记）
- 同一策略版本可对比 backtest vs live

#### [ ] 定时任务调度
**验收标准**：
- 以 APScheduler 为主，提供任务 CRUD、执行日志、失败重试
- 支持：定时回测、定时 Walk-Forward、定时生成报告

#### [ ] 账户管理与资金曲线
**验收标准**：
- 多交易账户绑定，余额/持仓定时同步
- 资金曲线历史记录与可视化
- 与实盘会话关联，记录每笔交易对余额的影响

#### [ ] 告警通知中心
**验收标准**：
- 多渠道通知：WebSocket、邮件、Webhook（飞书/钉钉/Slack）
- 告警规则配置：风控触发、任务完成/失败、策略信号、账户异动
- 告警历史记录与去重

---

### P2：多租户与平台化

#### [ ] 多用户/团队协作
- RBAC 权限控制、工作空间隔离
- 策略分享/订阅机制

#### [ ] 策略市场与社区分享
- 用户可将策略发布为"公开/私有"
- 其他用户可"fork"策略
- 评论/点赞/收藏功能

#### [ ] 监控告警
- Prometheus/Grafana 集成
- 关键指标告警、审计日志

#### [ ] 机器学习工作流
- 特征管道、训练/回测一体化
- 可解释性（SHAP）

#### [ ] 高频能力
- Tick 级回测
- 订单簿数据
- 滑点与延迟建模

#### [ ] 数据源插件化
- CSV/Parquet 导入
- 交易所 K 线
- 企业数据源（统一 schema + 数据质量校验）

#### [ ] 回放与调试
- 逐 bar 回放、断点/变量面板
- 关键事件时间线（订单/信号/风控）

#### [ ] 多交易所统一适配
- CCXT 之外支持更多本地化交易所（如 A 股券商接口）

#### [ ] 交易日历（TradingCalendar）
- 跳过非交易日（周末、节假日）
- 精确计算年化收益率和 Sharpe 比率
- 支持不同市场的交易日历

#### [ ] 回测预设与快速启动
- 常用回测配置模板（标的+策略+参数）
- 一键复用

#### [ ] 移动端适配
- 响应式 UI 或 PWA
- 支持基础查看与告警推送

#### [ ] SignalStrategy 简易模式
- 用户只需定义买卖信号，框架自动处理订单执行
- 适合初学者快速原型开发

#### [ ] 更多 Observer 可视化
- DrawDown Observer：实时追踪回撤时间序列
- Benchmark Observer：与基准指数实时对比
- GrossLeverage：杠杆使用情况追踪

#### [ ] 高级风控指标
- VaR / CVaR（风险价值）
- RecoveryFactor（恢复因子）
- PeriodStats（分阶段统计）

---

## 四、技术债（持续清理）

- [~] 后端/前端关键路径补齐最小测试
  - 已完成：核心 hooks 测试、storage 层测试、E2E 基础测试
  - 待补齐：更多边界条件测试、性能测试
- [ ] 性能基准：回测耗时、数据加载耗时、并发会话上限与压测脚本
- [ ] 文档：API 示例、常见故障排查、生产部署 checklist
- [ ] 代码重构：减少循环依赖，统一错误处理
- [ ] 日志标准化：统一日志格式、结构化日志输出、敏感信息脱敏

---

## 五、快速赢（Quick Wins）

以下功能在现有基础上添加成本最低：

| 功能 | 工作量 | 说明 |
|------|--------|------|
| UI 多 Timeframe 选择 | 10% | 后端已支持，主要是前端配置 |
| Replay vs Resample 选项 | 15% | 数据加载时增加 flag |
| 品种级手续费配置 | 20% | Portfolio 配置中增加 commission 字典 |
| StopTrail 订单支持 | 25% | CCXT adapter 已支持，需策略文档和前端参数 |

---

## 六、实现落点索引

| 模块 | 主要文件 |
|------|----------|
| 回测引擎 | `backend/src/service/backtest_engine.py`, `worker/backtest_worker.py` |
| 组合回测 | `backend/src/service/portfolio_backtest.py` |
| 深度分析 | `backend/src/service/deep_analysis.py` |
| Walk-Forward | `backend/src/routes/walkforward_routes.py` |
| 实盘交易 | `backend/src/service/live_engine.py`, `session_manager.py` |
| CCXT 适配 | `backend/src/brokers/ccxt_adapter/` |
| 策略模板 | `backend/src/service/strategy_templates.py` |
| 报告生成 | `backend/src/service/report_generator.py` |
| 前端配置 | `frontend/src/components/RunStrategy/StrategyConfigForm.jsx` |

---

*最后更新时间：2025-12-26*
