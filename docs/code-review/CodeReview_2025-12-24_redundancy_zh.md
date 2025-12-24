# Code Review：代码冗余与可维护性问题清单（2025-12-24）

- 审查范围：仅关注“代码实现层面”的冗余/重复实现与可维护性问题（不评价业务正确性/产品策略/性能压测结果）
- 仓库版本：`3b3cf33`
- 覆盖目录：`backend/`（重点 `backend/src/` + `backend/api.py`）、`frontend/src/`

---

## TL;DR（优先级最高的冗余/维护痛点）

1. **同一能力存在多套实现/入口**：任务执行（TaskManager vs 路由/TaskRoutes 内手写 executor）、WebSocket（`useWebSocket` vs `useTaskWebSocket`）、AI 分析（hook vs Modal/Page 内重复）。
2. **“复制/粘贴后增强”的核心安全/隔离代码**：`backend/src/service/strategy_executor.py` 明确从 `strategy_sandbox.py` 复制，策略白名单/危险内置函数策略容易漂移。
3. **接口字段命名不统一导致前端大量兼容分支**：如组合回测 individual result 使用 `return/sharpe/drawdown`，其他模块使用 `total_return/sharpe_ratio/max_drawdown`，造成 UI 侧转换和双格式兼容。
4. **路由层重复样板代码多且不一致**：`user_id = user.get("sub") if user else None`、try/except → HTTPException、lazy import 避免循环依赖等在多文件反复出现。
5. **超大文件承载多个职责**：`backend/src/service/report_generator.py`、`frontend/src/pages/*`（RunStrategy/PortfolioBacktest/BacktestHistory 等）包含“数据整形 + 状态机 + UI/模板渲染”混杂，修改成本高。

---

## 后端（backend）：冗余与不好维护点

### 1) 任务执行逻辑重复实现且出现“漂移/不一致风险”

- 位置：
  - `backend/src/service/task_manager.py`（统一任务生命周期/并发控制/WS 广播）
  - `backend/src/routes/backtest_routes.py`、`backend/src/routes/portfolio_routes.py`、`backend/src/routes/walkforward_routes.py`（各自提交任务/组织执行逻辑）
  - `backend/src/routes/task_routes.py`（`_get_executor_for_task_type()` 为 retry 再实现一套 executor 映射）
- 冗余/维护问题：
  - **同一 task 类型存在多套“executor 定义”**，容易出现参数签名、落库逻辑、返回结构不一致。
  - `backend/src/routes/task_routes.py` 内的 `deep_analysis_executor` 直接调用 `compute_deep_analysis(backtest_id=...)`，而 `backend/src/service/deep_analysis.py#compute_deep_analysis()` 实际签名需要 `equity_curve/start_date/end_date/...` ——这类漂移通常来自“复制一份简化实现”。
- 建议：
  - 把“task_type → executor”的注册表移到 `backend/src/service/`（单一事实来源），`task_routes.py` 只引用注册表，不再重复手写。
  - retry 逻辑建议复用“原始 task 提交时使用的 executor”（或把 executor 名称/版本写入 task record），避免“重试跑了另一段逻辑”。

### 2) 多处“全局单例/缓存”模式叠加，生命周期难追踪

- 位置：
  - 路由依赖注入：`backend/src/routes/common/dependencies.py` 使用 `@lru_cache(maxsize=1)` 提供 storage 单例
  - storage 自带单例：`backend/src/db/storage/report.py#get_report_storage()`、`backend/src/service/report_generator.py#get_report_generator()` 等
  - manager 自带单例：`backend/src/service/task_manager.py#get_task_manager()`、`backend/src/service/worker/worker_pool.py#get_worker_pool()`
- 冗余/维护问题：
  - “同一类对象”既可能由 FastAPI 依赖注入缓存，也可能由模块级 global 生成；排查资源泄漏/并发行为、写单测替换依赖时成本高。
- 建议：
  - 选一种单例策略即可：优先用 FastAPI 的依赖注入（或 app.state）管理生命周期；逐步移除 storage/service 内的 `global _xxx`。

### 3) 路由层重复的 user_id 提取与错误映射，未充分复用 common helpers

- 位置：
  - 重复 user_id：`backend/src/routes/*.py` 多处 `user_id = user.get("sub") if user else None`（如 `backtest_routes.py`、`settings_routes.py`、`report_routes.py`、`task_routes.py` 等）
  - 已有工具：`backend/src/routes/common/task_helpers.py#get_user_id()`、`map_exception_to_http()`
- 冗余/维护问题：
  - 明明已有 helper，实际使用不一致；同类路由易产生差异（例如某些 endpoint 允许匿名、某些不允许，错误返回格式也可能不同）。
- 建议：
  - 在 routes 层统一通过依赖注入拿到 `user_id`（例如 `Depends(get_optional_user_id)`），避免每个 endpoint 复制提取逻辑。
  - 将异常 → HTTP 的映射策略集中到全局 handler 或 `map_exception_to_http()`，减少 try/except 样板代码。

### 4) “为避免循环依赖的 lazy import”出现频繁，暴露模块耦合偏高

- 位置：
  - `backend/src/routes/backtest_routes.py`（`_get_task_storage()`、`_get_task_status()`）
  - `backend/src/service/task_manager.py`、`backend/src/brokers/ccxt_adapter/ccxt_broker.py` 等多处 “lazy import to avoid circular”
- 冗余/维护问题：
  - 每个模块都在“打补丁式”绕开循环依赖，长期会形成更多隐式耦合点和隐藏依赖链。
- 建议：
  - 将跨层共享的类型/常量下沉到更底层的 `src/types` 或 `src/contracts`（不 import service/routes），减少互相引用。

### 5) 策略沙箱/执行器存在复制实现，策略白名单与拦截规则容易漂移

- 位置：
  - `backend/src/service/strategy_sandbox.py`（soft sandbox）
  - `backend/src/service/strategy_executor.py`（subprocess executor，注释标明“Copied from strategy_sandbox.py with enhancements”）
- 冗余/维护问题：
  - `ALLOWED_IMPORTS` / 禁用 builtins / BLOCKED_ATTRIBUTES 等安全策略分别维护，更新一处漏另一处的概率很高。
- 建议：
  - 把“策略限制策略”（白名单、blocked attrs、危险关键字检查）抽到一个纯数据/纯函数模块（例如 `src/service/sandbox_policy.py`），两个执行路径共享引用。

### 6) 指标/字段命名在不同服务间不统一，引发上下游转换代码堆积

- 位置：
  - `backend/src/service/portfolio_backtest.py` 返回 `individual_results[].return/sharpe/drawdown`
  - `backend/src/db/storage/backtest.py` 与多个 routes/前端表格普遍使用 `total_return/sharpe_ratio/max_drawdown`
  - 影响到前端：`frontend/src/components/BacktestHistory/PortfolioDetailModal.jsx#getIndividualResults()` 需要同时兼容两种结构/字段名
- 冗余/维护问题：
  - UI 层不得不写“字段兼容/转换”分支，后续再加一个字段或改口径会牵一串文件。
- 建议：
  - 在后端输出层统一字段命名（建议统一为 `total_return/sharpe_ratio/max_drawdown`），并在一个地方做适配（例如 service 输出 DTO 或 routes 响应模型）。

### 7) 报告生成模块过于集中，ECharts 配置与数据整形强耦合

- 位置：`backend/src/service/report_generator.py`（尤其 `_add_chart_configs()` 内大量 ECharts dict）
- 冗余/维护问题：
  - 图表样式/主题/交互配置内联在 Python dict 中，后续新增图表或调整主题容易产生大量重复片段。
- 建议：
  - 将图表公共 theme 抽为常量/模板，按图表类型组合；或者把 ECharts option 下沉到前端统一渲染（后端只输出数据）。

---

## 前端（frontend）：冗余与不好维护点

### 1) WebSocket 连接/重连/心跳逻辑重复实现两套

- 位置：
  - `frontend/src/services/websocket.js`（`useWebSocket`，用于 live session）
  - `frontend/src/hooks/useTaskWebSocket.js`（用于 tasks channel）
- 冗余/维护问题：
  - 两套实现都包含：拼接 ws url、重连计数、heartbeat ping/pong、disconnect 清理；任何策略调整都要改两份，容易行为不一致。
- 建议：
  - 抽一个通用 `useWebSocketBase({ pathBuilder, onMessage, heartbeat, retryPolicy })`，task/live 只提供不同 path 和 message 处理器。

### 2) AI 分析逻辑在 Hook / Page / Modal 多处重复，状态管理分散

- 位置：
  - `frontend/src/hooks/useAIAnalysis.js`
  - `frontend/src/pages/RunStrategy.jsx`（构造 AI tab、管理 selectedModel/analyses 等）
  - `frontend/src/components/BacktestHistory/BacktestDetailModal.jsx`（再次实现一套 AI 分析、并落库）
- 冗余/维护问题：
  - 同一流程（选择模型→触发分析→展示结果→可选落库）在多个组件重复，容易出现提示词/输入口径不一致。
- 建议：
  - 将 AI 分析流程收敛到 hook（或 service + hook），Modal/Page 只组合 UI；落库（`updateBacktestAiAnalysis`）也作为可选回调注入，避免复制逻辑。

### 3) 策略参数处理（int/float coercion）在组件与 hook 重复

- 位置：
  - `frontend/src/hooks/useStrategyParams.js`（`handleParamChange`）
  - `frontend/src/components/RunStrategy/StrategyConfigForm.jsx`（组件内再次实现 `handleParamChange`）
- 冗余/维护问题：
  - 类型解析规则/默认值合并策略未来调整时要改两处，且两处可能出现不一致（例如空输入如何处理）。
- 建议：
  - StrategyConfigForm 直接使用 hook 提供的 `handleParamChange`（或抽 `coerceParamValue(type, value)` 工具函数）。

### 4) 大页面组件体积过大，包含大量内联子组件/样板逻辑

- 位置：
  - `frontend/src/pages/PortfolioBacktest.jsx`（页面文件内定义多个 UI 子组件）
  - `frontend/src/pages/BacktestHistory.jsx`（内联 `FilterBar`，并重复 fetch/pagination 逻辑）
  - `frontend/src/pages/RunStrategy.jsx`（tab 构建、AI UI、图表/日志组合都在同一文件）
- 维护问题：
  - 小改动容易牵动大量状态/渲染分支；可测试性差（很难对纯逻辑做单测）。
- 建议：
  - 拆分为 container（数据/状态）+ presentational（纯 UI）组件，并把“参数组装/分页计算/数据整形”下沉到 hooks/utils。

### 5) 前端需要做“后端返回结构兼容”的转换，属于上游不一致的下游冗余

- 位置：
  - `frontend/src/components/BacktestHistory/PortfolioDetailModal.jsx#getIndividualResults()`（同时兼容 array/object 两种格式，并对字段名做映射）
- 维护问题：
  - 该类兼容代码会在更多组件中蔓延，且 debug 成本高（哪个接口返回了哪种结构不直观）。
- 建议：
  - 后端统一返回 schema（推荐），或在前端 `services/` 层集中做一次 normalize（UI 只消费统一结构）。

### 6) 直接修改 props 对象（可导致难追踪的 UI 状态问题）

- 位置：`frontend/src/components/BacktestHistory/BacktestDetailModal.jsx`（`backtest.ai_analysis = ...`）
- 维护问题：
  - React 语义上 props 应视为只读；直接 mutation 可能导致父组件状态不同步、产生难复现问题。
- 建议：
  - 使用回调 `onAnalysisUpdate` 由父组件更新状态；Modal 内只维护本地 state，不修改传入对象。

---

## 建议的“最小重构顺序”（按投入产出比）

1. **后端：收敛 task executor 注册表**（解决多套实现漂移，避免 retry 逻辑跑错）
2. **前端：合并 WebSocket hook**（两处重复最多、行为最容易不一致）
3. **前后端：统一指标字段命名**（减少 UI 端字段映射与双结构兼容）
4. **前端：AI 分析与策略参数处理收敛到 hooks**（减少 Page/Modal 复制逻辑）
5. **逐步拆分巨型文件**（ReportGenerator、主要 pages），把纯逻辑下沉到 `utils/` 以便复用与单测

