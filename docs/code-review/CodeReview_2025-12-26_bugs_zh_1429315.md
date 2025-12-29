# Code Review：仅列 Bug 清单（2025-12-26）

- 审查范围：`backend/`、`frontend/`（仅关注会导致错误/异常/功能不可用的代码问题；不列风格/冗余/可维护性）
- 仓库版本：`1429315`

---

## 1) SQLAlchemy Model 的 `__repr__` 在 `total_return` 为空时会抛 `TypeError`

- 位置：
  - `backend/src/db/models/backtest.py:83`
  - `backend/src/db/models/backtest.py:146`
- 现象：当 `self.total_return is None` 时，`{self.total_return:.2f}` 会触发 `TypeError: unsupported format string passed to NoneType.__format__`，导致日志/调试打印对象时异常。
- 原因：f-string 中把 `if self.total_return else ...` 写成了字符串文字，并不会作为条件表达式生效。

## 2) `/api/analyze` 在 `metrics` 缺字段/为 `None` 时会 500

- 位置：`backend/src/routes/market_data_routes.py:349`（`analyze_results`）
- 现象：当 `metrics.returns` 或 `metrics.drawdown` 缺失/为 `None` 时，`returns > 0`、`{returns:.2f}`、`{drawdown:.2f}` 会抛 `TypeError`，导致接口返回 500。
- 相关行：`backend/src/routes/market_data_routes.py:349`、`:350`、`:352`、`:359`
- 原因：`AnalysisRequest.metrics` 未做字段校验与默认值处理。

## 3) Report 列表的 `status` 过滤参数在后端被忽略（前端过滤不生效）

- 位置：
  - `backend/src/routes/report_routes.py:114`（`list_reports` 签名缺少 `status`）
  - `backend/src/routes/report_routes.py:127`（调用 `storage.list_reports(...)` 未透传 `status`）
  - `frontend/src/services/reportApi.js:32`（前端会拼接 `status` query）
  - `frontend/src/hooks/useReports.js:41`（前端会设置/使用 `status` 过滤）
- 现象：前端选择 Report 状态过滤时返回结果不变（接口忽略 `status`）。
- 旁证：`backend/src/db/storage/report.py:158` 的 `list_reports` 已支持 `status` 过滤，但路由层未透传。

## 4) Task 列表接口暴露了 `sort_by/sort_order`，但实际不生效

- 位置：
  - `backend/src/routes/task_routes.py:84`（`list_tasks` 接受 `sort_by/sort_order`）
  - `backend/src/routes/task_routes.py:120`（调用 `manager.list_tasks(...)` 未透传排序参数）
  - `backend/src/service/task_manager.py:299`（`TaskManager.list_tasks` 不接受/不透传排序参数）
- 现象：客户端传 `sort_by` / `sort_order` 不会影响返回顺序（只能得到默认排序）。

## 5) Shared Report 页面无法正确区分 401/404（错误状态判断失效）

- 位置：
  - `frontend/src/services/reportApi.js:120`（错误只用 `res.statusText` 组装，不包含 status code）
  - `frontend/src/pages/SharedReport.jsx:42`、`:44`（用 `err.message.includes('401'/'404')` 判断）
- 现象：分享链接失效/不存在时，页面大概率落到 `unknown` 错误分支（显示 500），而不是“过期/未找到”。

