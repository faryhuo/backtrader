# Code Review：仅列 Bug 清单（2025-12-26）

- 审查范围：`backend/`、`frontend/`（仅关注“会导致错误/异常/功能不可用”的代码问题；不列风格/冗余/可维护性）
- 仓库版本：`f234b2c`

---

## 1) deep_analysis 任务重试必然失败（参数签名不匹配）

- 位置：`backend/src/routes/task_routes.py:408`（`deep_analysis_executor`）
- 现象：调用 `compute_deep_analysis(backtest_id=...)` 会触发 `TypeError: compute_deep_analysis() got an unexpected keyword argument 'backtest_id'`，导致 deep_analysis 类型任务在 `/api/tasks/{task_id}/retry` 重试时必然失败。
- 原因：`compute_deep_analysis` 的真实签名要求 `equity_curve/start_date/end_date/...`，见 `backend/src/service/deep_analysis.py:34`。

## 2) Backtest worker 初始化失败时，结果消息结构不兼容导致结果收集线程报错

- 位置：
  - `backend/src/service/worker/worker_pool.py:86`（`_backtest_worker_main` 的 ImportError 分支：`result_queue.put({"task_id":"INIT_ERROR","success":False,...})`）
  - `backend/src/service/worker/worker_pool.py:363`（`_collect_results`：`BacktestResult.from_dict(result_data)`）
  - `backend/src/service/worker/task_models.py:133`（`BacktestResult.from_dict` 最终 `return cls(**data)`，不接受多余字段）
- 现象：当 worker 进程无法 import `execute_backtest_task` 时，会向 result_queue 推送包含 `success` 字段的 dict；主进程收集结果时按 `BacktestResult` 反序列化会因“多余字段”抛 `TypeError`，导致结果收集线程对该消息处理失败（日志报错），并且无法把“初始化失败”的原因以统一的 BacktestResult 结构上报。

## 3) 前端单测文件引用未定义变量，导致 ESLint 直接报错（测试/CI 无法通过）

- 位置：`frontend/src/contexts/__tests__/SiteConfigContext.test.js:226`、`:239`、`:254`
- 现象：文件中使用 `siteApi.getSiteConfig...`，但 `siteApi` 未定义（该文件只 mock 并 import 了 `getSiteConfig`），ESLint 报 `no-undef`，`npm run lint` 失败。
