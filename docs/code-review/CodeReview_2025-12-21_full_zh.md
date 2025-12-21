# Backtrader 项目 Code Review 报告（中文）

- 审阅日期：2025-12-21
- 审阅范围：`backend/`、`frontend/`、`docs/`（排除 `frontend/node_modules/`、构建产物等）
- 参考版本：`git log -1` = `eed3881`（当前工作区存在未提交改动，以工作区内容为准）

## 1. 总体结论

项目整体完成度较高，后端分层清晰（`routes/service/db/brokers/utils`）、前端也有明确的 `pages/components/services` 分层，并且已经有一定数量的后端测试用例。最值得肯定的是：对“用户策略代码执行”的安全风险有明确意识，并实现了 Worker Pool/子进程校验等隔离机制与安全文档（`docs/SECURITY.md`）。

当前主要短板集中在两类：

1) **安全与边界假设**：策略代码依旧可能在 API 进程执行（某些路径/回退逻辑），并且默认配置允许 Worker 访问网络/写文件；对于多租户或公网部署风险较高。  
2) **前端认证与 API 调用一致性**：存在明显的实现缺陷（未定义变量、不同模块绕过统一 API 层），会导致部分功能在启用登录时不稳定或不可用。

## 2. 评分（10 分制）

| 维度 | 分数 | 说明 |
|---|---:|---|
| 架构与模块化 | 8.5 | 后端分层、前端分域 API 组织较好，职责边界明确 |
| 代码质量与一致性 | 7.6 | 大部分模块风格统一，但存在少量明显缺陷与不一致实现 |
| 安全性 | 7.0 | 有安全机制与文档，但“执行边界”与默认配置仍偏宽松 |
| 可维护性 | 8.0 | 文档与目录说明齐全，模块拆分合理 |
| 可靠性/异常处理 | 7.8 | 统一异常处理较好，但部分路径仍可能抛出不一致响应 |
| 测试与可验证性 | 7.8 | 后端已有较多 `pytest`，但前端缺少测试与端到端校验 |
| 文档与可上手性 | 8.5 | `README.md`、`docs/` 与目录说明较完整 |
| 性能与工程化 | 7.2 | Worker/绘图/大依赖较重，前端构建配置偏开发态 |
| **综合评分** | **7.8** | 可用于内部/单用户部署；若面向公网需先补齐安全与认证一致性 |

## 3. 亮点（做得好的地方）

### 3.1 后端

- 分层结构清晰：`backend/src/src.md`、`backend/src/service/service.md`、`backend/src/routes/routes.md` 对职责与约定写得比较完整。
- 全局异常处理集中：`backend/src/utils/exception_handlers.py` 统一封装错误结构并支持 DEBUG 模式。
- 策略文件名做了路径穿越防护：`backend/src/service/backtest_engine.py` 的 `_sanitize_strategy_name()` 对策略名做白名单校验。
- Worker Pool 架构可扩展：`backend/src/service/worker/worker_pool.py` 将回测/实盘执行隔离到子进程，避免主进程加载 backtrader 等重依赖。
- 凭证加密：`backend/src/utils/encryption.py` 使用 Fernet 对敏感字段加密存储，并提供脱敏展示。
- 后端测试数量可观：`backend/tests/` 覆盖 routes/config/utils/service/brokers 等多个层级。

### 3.2 前端

- 目录分层明确：`frontend/src/src.md`、`frontend/src/services/services.md`、`frontend/src/components/components.md` 对组织方式有约定。
- 统一 API 核心层：`frontend/src/services/apiCore.js` 提供 `buildRequest/parseResponse`，并在多数域 API 中复用。
- i18n 支持较完整：`frontend/src/locales/` 具备中英文文案基础。

## 4. 主要问题与风险（按优先级）

### P0（建议优先修复）

1) 前端存在未定义变量，潜在运行时错误  
   - 文件：`frontend/src/services/apiCore.js`  
   - 问题：`getAccessToken()` 使用 `API_RESOURCE`，但该变量在项目中未定义（当前仅此处引用）。  
   - 影响：若该导出方法被调用，会直接抛 `ReferenceError`；同时也会误导后续开发者。  
   - 建议：删除该导出或改为使用 `API_URL`（或显式引入“resource identifier”常量），并补一个最小单测/自检。

2) 前端 `siteApi` 绕过统一 API 层，且使用不存在的本地 token 机制  
   - 文件：`frontend/src/services/siteApi.js`  
   - 问题：使用 `localStorage.getItem('auth_token')` 构造 Bearer，但项目其余认证通过 Logto 的 `getAccessToken` 注入；代码库也没有写入 `auth_token` 的地方。  
   - 影响：启用登录时，`/site/config/admin`、`PUT /site/config`、`POST /site/config/reset` 很可能无法鉴权成功；同时错误处理与全局 401 行为不一致。  
   - 建议：将该文件改造成与 `settingsApi.js` 一致：基于 `buildRequest/parseResponse`；避免引入“第二套 token 存储”。

3) “策略代码不在 API 进程执行”的文档/实现口径不一致  
   - 文件：  
     - `backend/src/service/service.md`（宣称主进程不执行用户策略）  
     - `backend/src/service/backtest_engine.py` 的 `load_user_strategy()`（子进程校验后仍会在主进程 `execute_strategy_code()`）  
     - `docs/SECURITY.md`（明确提示校验后会在主进程执行）  
   - 影响：容易造成错误的安全预期；在公网/多用户场景下属于高风险点。  
   - 建议：统一口径（以 `docs/SECURITY.md` 为准），并在代码中显式标注：**主进程执行仅适用于“受信任策略”**；更进一步的方案是将“类对象加载/执行”也放到 Worker/容器内（例如通过 IPC 传结果而非传 class）。

4) Worker 默认允许网络/写文件，扩大了“用户策略”可做的事情  
   - 文件：`backend/src/config/worker_config.py`  
   - 问题：`allow_network`、`allow_file_write` 默认 `true`；但 Worker 会执行用户策略代码（即便有软沙箱）。  
   - 影响：在策略不受信任时，可能发生数据外传、扫描内网、写入磁盘等问题。  
   - 建议：区分 backtest/live 两类 worker 的默认能力：回测默认关闭网络与写盘（仅在需要生成图表时短暂开放写盘），实盘再按需开放。

### P1（中优先级）

1) JWT 验证建议固定允许的算法集合  
   - 文件：`backend/src/utils/auth.py`  
   - 现状：`verify_token()` 读取 header 中的 `alg` 并作为允许算法传给 `jwt.decode()`。  
   - 风险：在配置或依赖行为变化下可能扩大攻击面；更稳妥方式是仅接受期望算法（例如 `RS256`）。  
   - 建议：在配置中增加 `LOGTO_JWT_ALGS`（默认 `RS256`），并在 `jwt.decode()` 时使用固定列表。

2) 前端 401 处理与登录体验存在偏差  
   - 文件：`frontend/src/services/apiCore.js`、`frontend/src/App.jsx`  
   - 现状：`parseResponse` 遇到 401 会跳转 `/login`，但路由里 `/login` 直接重定向到 `/`，并不会触发 Logto 的 `signIn()`。  
   - 建议：把“触发登录”的动作从 URL 跳转调整为调用 `signIn()`（可以通过 Provider 注入一个全局回调给 `apiCore`），或在 `/login` 页面真正执行一次登录跳转。

3) 构建配置偏开发态  
   - 文件：`frontend/vite.config.js`  
   - 现状：`build.sourcemap=true` 且 `minify=false`。  
   - 影响：产物体积偏大、暴露源码细节；生产部署不建议默认如此。  
   - 建议：通过环境变量区分 dev/prod：prod 开启 minify，sourcemap 按需开启。

4) Python 依赖未锁定版本  
   - 文件：`backend/requirements.txt`  
   - 现状：使用 `>=`，可复现性较弱。  
   - 建议：提供 `requirements-lock.txt`（pip-tools/uv）或改用 Poetry/uv lock，至少为生产部署锁定版本。

### P2（低优先级/体验优化）

- `backend/src/utils/encryption.py` 在模块导入时执行 `load_dotenv()`，属于“导入即产生副作用”；建议统一由 `config/settings.py` 负责加载环境变量，工具模块尽量纯函数化。
- 多处模块级单例（例如 storage/manager）在测试/并发场景下可能引入状态污染；可以逐步切换为依赖注入或 `lru_cache` 形式。

## 5. 建议的改进路线（可执行）

### 5.1 一周内可完成（高收益）

- 修复前端 P0：统一 `siteApi` 到 `apiCore`，清理 `API_RESOURCE` 未定义问题，并补最小自测。
- 将“策略执行边界”写入 `README.md` / `docs/SECURITY.md` 的显眼位置，并在 UI/配置中明确标注“仅限受信任环境”。
- 将 Worker 的网络/写盘默认能力收紧（至少对 backtest worker 收紧），并在 `.env.template` 中补齐相关开关说明。

### 5.2 中期（面向公网/多用户）

- 将策略执行迁移到更强隔离：容器化（`SANDBOX_MODE=docker`）+ `--network=none` + 只读挂载策略目录；或将所有执行都放入 Worker/Job 系统（主进程只做调度）。
- 引入端到端验证：至少覆盖“登录开启/关闭两种模式”的关键流程（回测、策略保存、实盘启动、WebSocket 连接、设置页）。

## 6. 附录：快速定位清单

- 后端入口：`backend/main.py`、`backend/api.py`
- 策略执行/隔离：`backend/src/service/backtest_engine.py`、`backend/src/service/isolated_sandbox.py`、`backend/src/service/worker/worker_pool.py`
- 认证：`backend/src/utils/auth.py`
- 前端 API 核心：`frontend/src/services/apiCore.js`
- 站点配置 API：`frontend/src/services/siteApi.js`

