# Project Test Case List（基于项目代码）

本文档基于当前项目实现（`backend/src/routes/*`、`backend/src/service/*`、`backend/src/utils/*`、`frontend/src/*`）整理应覆盖的测试用例清单，用于规划自动化与回归范围；不依赖现有测试脚本。

## 约定

- **优先级**：P0（核心主路径/安全/数据破坏风险）> P1（常用功能/边界）> P2（低频/体验）
- **类型**：UNIT（单元）/ API（接口契约）/ INTEG（集成：DB/文件/任务）/ E2E（端到端：前后端+WebSocket）
- **预期**：除明确标注公开端点外，默认 API 需要鉴权（`get_current_user`）。

---

## Backend API（按路由模块）

### SITE：站点配置（`backend/src/routes/site_config_routes.py`）

| ID | 场景 | 入口 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| SITE-001 | 未登录可读取站点配置 | `GET /api/site/config` | API | P0 |
| SITE-002 | 返回结构包含 `site/links/stats/features` | `GET /api/site/config` | API | P0 |
| SITE-003 | 读取 admin 配置需要鉴权 | `GET /api/site/config/admin` | API | P0 |
| SITE-004 | 更新配置：仅更新非空字段，返回 updated_fields | `PUT /api/site/config` | API/INTEG | P1 |
| SITE-005 | 更新配置：空 body 或全 None 返回 400 | `PUT /api/site/config` | API | P1 |
| SITE-006 | reset 配置：需要鉴权，成功后回落到 env/default | `POST /api/site/config/reset` | API/INTEG | P1 |

### STRATEGY：策略管理（`backend/src/routes/strategy_routes.py`）

| ID | 场景 | 入口 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| STR-001 | 列表：鉴权必需，返回 `{"strategies":[...]}` | `GET /api/strategies` | API | P0 |
| STR-002 | 获取策略：name 为空时返回第一个策略或 404 | `GET /api/strategy?name=` | API | P1 |
| STR-003 | 获取策略：不存在/加载失败返回 400（StrategyLoadError） | `GET /api/strategy?name=...` | API | P1 |
| STR-004 | 保存策略：写入文件成功，返回 status ok | `POST /api/strategy` | API/INTEG | P0 |
| STR-005 | 保存策略：非法策略名（路径穿越/非法字符）被拒绝 | `POST /api/strategy` | API/SEC | P0 |
| STR-006 | 参数提取：提取失败时返回空数组且不报错 | `GET /api/strategy/{name}/params` | API | P1 |
| STR-007 | 模板列表：返回 templates/categories/difficulties | `GET /api/templates` | API | P1 |
| STR-008 | 模板详情：不存在返回 404 | `GET /api/templates/{template_id}` | API | P1 |
| STR-009 | 导入模板：策略名为空/已存在返回 400；成功写入新策略 | `POST /api/templates/import` | API/INTEG | P1 |
| STR-010 | 版本列表：分页 limit/offset 生效且只返回当前用户版本 | `GET /api/strategy/{name}/versions` | API/INTEG | P1 |
| STR-011 | 最新版本：没有版本返回 404 | `GET /api/strategy/{name}/versions/latest` | API | P2 |
| STR-012 | 版本对比/回滚/读取指定版本：非法 version/无权限返回 4xx | `.../compare`、`.../rollback` | API/INTEG | P2 |

### BACKTEST：回测（`backend/src/routes/backtest_routes.py`）

| ID | 场景 | 入口 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| BT-001 | 提交回测任务：返回 task_id，状态为 pending/running | `POST /api/backtest` | API/INTEG | P0 |
| BT-002 | 回测请求校验：缺字段/日期格式/现金<=0 等返回 422/400 | `POST /api/backtest` | API | P0 |
| BT-003 | 回测执行失败映射到正确 HTTP（`map_exception_to_http`） | `POST /api/backtest` | API | P1 |
| BT-004 | 历史列表：过滤/排序/分页生效 | `POST /api/backtest/history` | API/INTEG | P0 |
| BT-005 | 历史详情：不存在返回 404；只允许访问本人记录 | `GET /api/backtest/history/{id}` | API/SEC | P0 |
| BT-006 | 删除回测：删除 DB 记录并处理关联图片文件 | `DELETE /api/backtest/history/{id}` | API/INTEG | P1 |
| BT-007 | 更新 AI 分析：不存在返回 404；写入按 model_name 合并 | `POST /api/backtest/history/{id}/ai-analysis` | API/INTEG | P1 |
| BT-008 | 深度分析：有缓存直接返回；无 equity_curve 返回 400 | `POST /api/backtest/history/{id}/deep-analysis` | API/INTEG | P1 |
| BT-009 | 深度分析：benchmarks/rolling_window/risk_free_rate 入参校验 | `POST /api/backtest/history/{id}/deep-analysis` | API | P2 |

### MARKET DATA：行情与缓存（`backend/src/routes/market_data_routes.py`）

| ID | 场景 | 入口 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| MD-001 | ticker 元信息：非法 ticker 返回统一验证错误 | `GET /api/ticker/{ticker}/info` | API | P0 |
| MD-002 | 价格数据：返回 `{"data": ...}` 且时间区间生效 | `GET /api/ticker/{ticker}/prices` | API/INTEG | P0 |
| MD-003 | 兼容旧接口：返回 ticker_info + data | `POST /api/data` | API | P1 |
| MD-004 | cache stats：返回整体统计结构 | `GET /api/cache/stats` | API/INTEG | P1 |
| MD-005 | cache cleanup：未提供任何过滤条件必须 400（防全删） | `DELETE /api/cache/cleanup` | API/SEC | P0 |
| MD-006 | cache warmup：多 ticker 部分失败可返回成功/失败计数 | `POST /api/cache/warmup` | API/INTEG | P2 |
| MD-007 | 删除单 ticker cache：不存在返回 404 | `DELETE /api/cache/{ticker}` | API | P2 |
| MD-008 | resample：非法 source/target 或路径不允许返回 400 | `POST /api/resample` | API | P1 |
| MD-009 | analyze：缺少 metrics/结构错误返回 422/400 | `POST /api/analyze` | API | P2 |

### LIVE：实盘/模拟盘（`backend/src/routes/live_routes.py`）

| ID | 场景 | 入口 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| LIVE-001 | start：mode 只允许 paper/live；非法 mode 返回 400 | `POST /api/live/start` | API | P0 |
| LIVE-002 | start：live 模式在 `LIVE_TRADING_ENABLED=false` 时返回 403 | `POST /api/live/start` | API/SEC | P0 |
| LIVE-003 | start：exchange/symbol/timeframe 校验失败返回 400 | `POST /api/live/start` | API | P0 |
| LIVE-004 | stop：session 不存在返回 404；已停止返回 400 | `POST /api/live/stop` | API | P1 |
| LIVE-005 | status/sessions：只返回本人会话数据 | `GET /api/live/status/{id}`、`GET /api/live/sessions` | API/SEC | P0 |
| LIVE-006 | exchanges：仅返回 enabled exchanges，字段完整 | `GET /api/live/exchanges` | API | P1 |
| LIVE-007 | orders：session 不存在/无权限返回 4xx | `GET /api/live/orders/{id}` | API | P2 |
| LIVE-008 | health：健康/异常时返回结构一致（healthy/unhealthy） | `GET /api/live/health` | API | P1 |

### PORTFOLIO：组合回测（`backend/src/routes/portfolio_routes.py`）

| ID | 场景 | 入口 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| PF-001 | 提交组合回测任务：tickers/weights 数量不一致返回 400 | `POST /api/portfolio/backtest` | API | P0 |
| PF-002 | 提交成功返回 task_id；结果由 Task 流转 | `POST /api/portfolio/backtest` | API/INTEG | P1 |
| PF-003 | 历史列表：分页/排序参数生效 | `GET /api/portfolio/history` | API/INTEG | P1 |
| PF-004 | 详情：不存在返回 404；只允许访问本人记录 | `GET /api/portfolio/{id}` | API/SEC | P0 |
| PF-005 | 删除：不存在返回 404 | `DELETE /api/portfolio/{id}` | API | P2 |

### WALKFORWARD：参数优化（`backend/src/routes/walkforward_routes.py`）

| ID | 场景 | 入口 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| WF-001 | start：param_grid 为空/非法结构返回 422/400 | `POST /api/walkforward/start` | API | P1 |
| WF-002 | start：train/test 天数下限（ge=30/ge=7）生效 | `POST /api/walkforward/start` | API | P1 |
| WF-003 | list：过滤/分页/排序参数生效 | `GET /api/walkforward/list` | API/INTEG | P2 |
| WF-004 | get/status：不存在返回 404；若有用户隔离则不可越权访问 | `GET /api/walkforward/{id}`、`GET /api/walkforward/{id}/status` | API/SEC | P1 |
| WF-005 | delete：不存在返回 404 | `DELETE /api/walkforward/{id}` | API | P2 |

### TASKS：任务管理（`backend/src/routes/task_routes.py`）

| ID | 场景 | 入口 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| TASK-001 | list：非法 task_type/status 返回 400（枚举校验） | `GET /api/tasks` | API | P0 |
| TASK-002 | list：user 为空时走可选鉴权；不泄露他人任务 | `GET /api/tasks` | API/SEC | P0 |
| TASK-003 | stats：返回并发/运行/待执行等统计结构 | `GET /api/tasks/stats` | API | P1 |
| TASK-004 | cancel：仅 pending/running 可取消；其余返回 400 | `POST /api/tasks/{id}/cancel` | API | P1 |
| TASK-005 | retry：仅 failed/cancelled 可重试；生成新任务 | `POST /api/tasks/{id}/retry` | API/INTEG | P2 |
| TASK-006 | delete：running 且 force=false 返回 400；force=true 可删 | `DELETE /api/tasks/{id}?force=` | API | P2 |

### REPORTS：报告中心（`backend/src/routes/report_routes.py`）

| ID | 场景 | 入口 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| RPT-001 | 生成报告：report_type 枚举校验，source_ids 不能为空 | `POST /api/reports` | API | P0 |
| RPT-002 | 生成报告：创建记录后后台任务运行，状态可轮询 | `POST /api/reports`、`GET /api/reports/{id}` | INTEG | P1 |
| RPT-003 | download：仅 COMPLETED 可下载；文件缺失返回 404 | `GET /api/reports/{id}/download` | API/INTEG | P1 |
| RPT-004 | share：仅 COMPLETED 可分享；expires_in_hours 范围生效 | `POST /api/reports/{id}/share` | API | P1 |
| RPT-005 | revoke：撤销分享后 share_token 失效 | `DELETE /api/reports/{id}/share` | API/INTEG | P2 |
| RPT-006 | public shared：token 过期/签名错误返回 401 | `GET /api/reports/shared/{share_token}` | API/SEC | P0 |

### AI：图表分析（`backend/src/routes/ai_routes.py`）

| ID | 场景 | 入口 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| AI-001 | 未配置 OpenAI key/base_url 返回 500 且提示配置路径 | `POST /api/ai_analyze` | API | P1 |
| AI-002 | 支持纯文本 message | `POST /api/ai_analyze` | API/INTEG | P2 |
| AI-003 | 支持图片上传：base64 编码并调用模型 | `POST /api/ai_analyze` | API/INTEG | P2 |
| AI-004 | 配置 proxy 时使用 httpx AsyncClient(proxy=...) | `POST /api/ai_analyze` | INTEG | P2 |

### FRONTEND：静态托管（`backend/src/routes/frontend_routes.py`）

| ID | 场景 | 入口 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| FE-001 | 未构建前端时 `/` 返回 JSON 提示 | `GET /` | API | P1 |
| FE-002 | 构建后 `/` 返回 index.html | `GET /` | E2E | P1 |
| FE-003 | SPA catch-all：非 API 路由返回 index.html | `GET /some/route` | E2E | P2 |
| FE-004 | 图片静态目录 `/images/*` 可访问 | `GET /images/{file}` | INTEG | P2 |
| FE-005 | `/assets/*` 仅在存在时挂载 | `GET /assets/{file}` | INTEG | P2 |

### WS：WebSocket（`backend/src/routes/websocket_routes.py`）

| ID | 场景 | 入口 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| WS-001 | live ws：session 不存在，服务器 close(code=1008) | `WS /ws/live/{session_id}` | E2E | P1 |
| WS-002 | live ws：token 缺失/错误，服务器 close(code=1008) | `WS /ws/live/{session_id}?token=` | E2E/SEC | P0 |
| WS-003 | live ws：发送 ping 得到 pong | `WS /ws/live/{session_id}` | E2E | P1 |
| WS-004 | tasks ws：连接成功后可收到 task_created/progress 等事件 | `WS /ws/tasks` | E2E | P2 |

---

## Backend UNIT/INTEG（按工具/服务）

### 配置与安全

| ID | 场景 | 代码位置 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| UTIL-001 | share token：签名正确可验证；篡改任一段验证失败 | `backend/src/utils/share_token.py` | UNIT | P0 |
| UTIL-002 | share token：过期 token verify 返回 None | `backend/src/utils/share_token.py` | UNIT | P0 |
| UTIL-003 | broker_config：缺文件抛 FileNotFoundError；错误 JSON/结构抛异常 | `backend/src/utils/config_loader.py` | UNIT | P1 |
| UTIL-004 | exchange config：disabled/不存在/adapter 非 ccxt/ibkr 返回 ValueError | `backend/src/utils/config_loader.py` | UNIT | P1 |

### 凭证校验（可能需要网络/第三方）

| ID | 场景 | 代码位置 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| CRED-001 | openai key：空 key 返回 (False, msg) | `backend/src/utils/credential_validator.py` | UNIT | P2 |
| CRED-002 | ccxt：空 key/secret 返回 (False, msg) | `backend/src/utils/credential_validator.py` | UNIT | P2 |
| CRED-003 | ccxt：异常类型映射为可读 message（Auth/Network 等） | `backend/src/utils/credential_validator.py` | UNIT | P2 |

### 任务/并发/请求上下文

| ID | 场景 | 代码位置 | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| TASKM-001 | task 状态流转：pending→running→completed/failed，progress 单调 | `backend/src/service/task_manager.py` | INTEG | P1 |
| CTX-001 | request_id/trace_id：每请求生成/透传一致 | `backend/src/utils/request_context.py` | UNIT/INTEG | P2 |

---

## Frontend（基于页面与交互）

| ID | 场景 | 位置（建议） | 类型 | 优先级 |
| --- | --- | --- | --- | --- |
| UI-001 | 登录开关：`/api/site/config` 的 loginEnabled 控制 UI 行为 | `frontend/src/pages/*` | E2E | P1 |
| UI-002 | 策略管理：列表/编辑/保存失败提示（401/500） | `frontend/src/components/StrategyMaintain/*` | E2E | P0 |
| UI-003 | 回测：提交任务→任务进度→历史列表可见 | `frontend/src/components/RunStrategy/*` | E2E | P0 |
| UI-004 | 深度分析：无 equity_curve 时提示用户重跑回测 | `frontend/src/components/BacktestHistory/*` | E2E | P1 |
| UI-005 | 数据源设置：校验与保存、错误提示、重置 | `frontend/src/components/DataSource/*` | E2E | P1 |
| UI-006 | 实盘：start/stop 会话；WebSocket token 缺失时提示重连/失败 | `frontend/src/components/LiveTrading/*` | E2E | P1 |
| UI-007 | 报告中心：生成→轮询状态→下载/分享→打开分享链接 | `frontend/src/pages/*` | E2E | P1 |
| UI-008 | 国际化：中英切换后关键文案覆盖（不出现 key 原文） | `frontend/src/locales/*` | E2E | P2 |

---

## 示例测试用例（文本版）

### WS-002：live WebSocket token 鉴权

- 目的：防止未授权订阅实盘会话的实时数据（`/ws/live/{session_id}`）。
- 前置：存在 session（由 `POST /api/live/start` 创建），且 session 有 ws_token。
- 步骤：
  1. 连接 `WS /ws/live/{session_id}`，不带 `token` 或带错误 `token`
  2. 观察服务端关闭连接
- 预期：
  - 服务端关闭连接，close code = `1008`，reason 为 `Invalid or missing token`

