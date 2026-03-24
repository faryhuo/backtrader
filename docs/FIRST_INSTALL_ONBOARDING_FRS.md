# 首次安装引导页 FRS

## 1. 文档目标

本文档定义“首次安装引导页（First-Run Setup Wizard）”的产品与功能需求，目标是帮助用户在第一次启动系统时，完成最小可用配置，并按需开启认证、AI、数据源与实盘交易能力。

本文档基于当前代码实现整理，覆盖：
- 需要配置的 `env` 与 `config` 项
- 必填 / 条件必填 / 可选的分类
- 每个配置项的作用、类型、范围、默认值与生效条件
- 推荐配置顺序
- 首次安装引导页的信息架构、交互流程与验收标准

## 2. 设计目标

### 2.1 核心目标
- 让用户在不了解项目内部结构的情况下完成首次可运行配置。
- 明确区分“启动必须配置”和“功能增强配置”，避免一次性展示过多高级项。
- 将配置顺序设计为：先完成基础运行，再按能力逐步开启。
- 对敏感配置提供风险提示、格式校验、默认值说明与来源说明。

### 2.2 设计原则
- 最小可用优先：先确保系统能启动、能访问、能保存配置。
- 条件暴露：只有当用户开启某个能力时，才显示对应配置项。
- 明示优先级：说明配置最终来自 `.env` / `json` / 数据库 / 默认值中的哪一层。
- 安全默认：默认关闭登录、默认关闭实盘、默认使用 paper 模式、默认不开放跨域凭证。
- 可回看：在最终确认页展示“将写入哪些文件、哪些值仍未配置、哪些功能暂不可用”。

## 3. 当前实现中的配置来源与优先级

### 3.1 主要配置文件
- `backend/.env`：后端环境变量，包含加密、认证、AI、CORS、交易开关等。
- `backend/resources/config/database_config.json`：数据库类型与路径配置。
- `backend/resources/config/strategy_config.json`：策略目录、沙箱、Worker Pool 配置。
- `backend/resources/config/broker_config.json`：交易所、风控、交易参数配置。
- `backend/resources/config/report_config.json`：报告输出目录与导出配置。
- `backend/resources/config/logger_config.json`：日志输出配置。

### 3.2 运行时优先级
- 通用凭证类配置：数据库设置 > `.env` > 代码默认值。
- 数据库连接：`DATABASE_URL` > `database_config.json` > 默认 SQLite (`backend/trading_sessions.db`)。
- 报告配置：`report_config.json` > `report_config.template.json` > 内置默认值。
- Logto 前端配置：数据库 > `LOGTO_*` / `VITE_LOGTO_*` > 关闭登录。

### 3.3 首次安装页的建议写入目标
首次安装引导页建议只写入以下文件，不直接写数据库：
- `backend/.env`
- `frontend/.env`
- `backend/resources/config/database_config.json`
- `backend/resources/config/strategy_config.json`
- `backend/resources/config/broker_config.json`
- `backend/resources/config/report_config.json`
- `backend/resources/config/logger_config.json`

原因：首次安装阶段数据库中的用户设置、登录体系与加密密钥尚未稳定，文件写入更符合初始化场景。

## 4. 配置项盘点与分类

### 4.1 P0：首次启动建议必须完成

这部分配置决定“系统是否可安全进入可用状态”。

| 配置项 | 来源 | 必填级别 | 作用 | 类型 / 范围 | 默认 / 回退 | 说明 |
|---|---|---|---|---|---|---|
| `ENCRYPTION_KEY` | `backend/.env` | 强必填 | 用于加密保存 OpenAI、交易所、EODHD 等敏感凭证 | string；非空；建议 Fernet key 或高强度随机字符串 | 无安全默认值；缺失时保存/解密凭证会失败 | 虽然应用可在部分场景下启动，但首次安装页应强制要求填写或生成 |
| `ENABLE_LOGIN` | `backend/.env` | 必填 | 明确是否启用登录认证 | boolean；`true/false` | 模板默认 `false` | 必须显式写入，避免后端默认值与前端展示默认值不一致 |
| `DATABASE_URL` 或 `database.type + sqlite.path` | `backend/.env` / `database_config.json` | 二选一必填（向导可自动填默认） | 决定数据存储位置 | `DATABASE_URL` 为 SQLAlchemy URL；或 `sqlite/postgresql` 配置 | 未配置时回退到 `sqlite:///backend/trading_sessions.db` | 向导可默认选择 SQLite，本质上可免手填，但页面必须让用户确认存储方案 |


### 4.2 P1：按功能开启时必须完成

| 配置项 / 组 | 来源 | 何时必填 | 作用 | 类型 / 范围 | 默认 / 回退 |
|---|---|---|---|---|---|
| Logto 认证组：`LOGTO_ISSUER`、`LOGTO_JWKS_URI`、`LOGTO_AUDIENCE`、`LOGTO_REQUIRED_SCOPES`、`LOGTO_ENDPOINT`、`LOGTO_APP_ID`、`LOGTO_REDIRECT_URI`、`LOGTO_POST_LOGOUT_REDIRECT_URI` | `backend/.env` | 用户打开“启用登录”时 | 后端校验 JWT，前端发起 OAuth 登录 | URL / string；`LOGTO_REQUIRED_SCOPES` 为空格分隔 scope 字符串 | 未配置时前端会自动禁用登录 |
| OpenAI 组：`OPENAI_API_KEY`、`OPENAI_BASE_URL` | `backend/.env` | 用户开启 AI 分析时 | 驱动 AI 分析与策略解释能力 | API key string；`OPENAI_BASE_URL` 为 URL | `OPENAI_BASE_URL` 默认 `https://api.openai.com/v1` |
| EODHD 数据源组：`EODHD_API_KEY` + 数据源优先级 | `.env` / 数据库设置 | 用户选择 EODHD 作为数据源时 | 提供 Yahoo 之外的数据行情来源 | API key string；优先级为 `yahoo/eodhd/database` 数组 | 默认优先级 `['yahoo', 'database']` |
| 实盘总开关：`LIVE_TRADING_ENABLED` | `backend/.env` | 用户开启 live mode 时 | 放开实盘接口能力 | boolean | 默认 `false` |
| 交易所凭证组：`CCXT_{EXCHANGE}_{MODE}_API_KEY`、`SECRET`、`PASSPHRASE` | `backend/.env` 或数据库设置 | 用户启用对应交易所的 `paper/live` 模式时 | 连接 Binance / OKX / Bybit | string；OKX 额外需要 `PASSPHRASE` | 无默认值 |
| CORS 组：`CORS_ALLOW_ORIGINS`、`CORS_ALLOW_ORIGIN_REGEX`、`CORS_ALLOW_CREDENTIALS` | `backend/.env` | 前后端跨域部署或跨域登录时 | 控制浏览器跨域访问 | origins 为逗号分隔列表或 `*`；regex 字符串；credentials 为 boolean | 模板默认 `*` + `false` |

### 4.3 P2：可选增强配置

| 配置项 / 文件 | 作用 | 类型 / 范围 | 默认 / 回退 | 首装是否建议展示 |
|---|---|---|---|---|
| `HTTP_PROXY`、`HTTPS_PROXY` | 后端访问外部网络时走代理 | URL | 空 | 放到“高级网络”折叠区 |
| `HOST`、`PORT` | 控制后端监听地址 | `HOST` string；`PORT` int `1-65535` | `0.0.0.0` / `8000` | 可选，高级区 |
| `LOG_LEVEL` | 控制日志级别 | enum：`DEBUG/INFO/WARNING/ERROR/CRITICAL` | `INFO` | 可选，高级区 |
| `DEBUG` | 是否返回更详细错误信息 | boolean | `false` | 仅开发环境显示 |
| `MAX_CONCURRENT_TASKS` | 后台任务并发数 | int，建议 `>=1` | `3` | 可选，高级区 |
| `REPORT_SHARE_SECRET` | 报告分享 token 签名密钥 | string；生产需高强度随机值 | 默认弱值，仅开发可接受 | 若启用公开分享，建议必填 |
| `REPORT_MAX_AGE_DAYS` | 分享链接最大有效期 | int，建议 `>=1` | `30` | 可选 |
| `SITE_*` 站点品牌组 | 落地页标题、描述、链接与统计数字 | string | 有默认值 | 可选，可放最后一步 |
| `logger_config.json` | 控制日志输出到控制台/文件 | JSON | 已有默认配置 | 可选，高级区 |
| `report_config.json` | 控制报告输出目录 / PDF 参数 | JSON | 已有默认配置 | 可选，高级区 |
| `strategy_config.json` | 控制策略目录、沙箱、Worker Pool | JSON | 已有默认配置 | 建议展示基础项，高级项折叠 |
| `broker_config.json` | 控制交易所启用、风控限制、支持周期 | JSON | 已有默认配置 | 若用户要做实盘/模拟盘，则展示 |

## 5. 每个配置项的作用、类型与范围

### 5.1 基础运行与安全

#### `ENCRYPTION_KEY`
- 作用：加密数据库中保存的敏感值，如 OpenAI key、交易所 API key、EODHD key。
- 类型：string。
- 范围：非空；建议 32-byte Fernet key；也兼容任意字符串，但不建议弱口令。
- 页面要求：
  - 提供“一键生成”按钮。
  - 默认隐藏真实值，仅支持复制。
  - 文案提示“后续修改该值会导致历史已加密凭证无法解密”。

#### `ENABLE_LOGIN`
- 作用：控制是否启用认证。
- 类型：boolean。
- 范围：`true` / `false`。
- 页面要求：
  - 默认 `false`。
  - 若为 `false`，隐藏整个 Logto 详细表单。
  - 若为 `true`，Logto 字段必须全部进入校验。

#### 数据库连接

1) `DATABASE_URL`
- 作用：直接指定数据库连接串。
- 类型：string。
- 范围：SQLAlchemy URL，例如：
  - `sqlite:///D:/data/trading_sessions.db`
  - `postgresql://user:pass@host:5432/trading`
- 页面要求：高级模式可直接填写。

2) `database_config.json`
- `database.type`
  - 类型：enum，当前建议 `sqlite` 或 `postgresql`。
- `database.sqlite.path`
  - 类型：string。
  - 范围：相对路径或绝对路径。
  - 推荐：默认 `trading_sessions.db`。
- `database.postgresql.host`
  - 类型：string。
- `database.postgresql.port`
  - 类型：int，建议 `1-65535`，默认 `5432`。
- `database.postgresql.database`
  - 类型：string。
- `database.postgresql.username`
  - 类型：string。
- `database.postgresql.password`
  - 类型：string。
- 注意：`database_config.json` 中的 `wal_mode`、`timeout_seconds`、`pool_size`、`max_overflow`、`backup`、`maintenance` 等字段当前代码未实际消费，不建议在首版向导中重点暴露，可放在“预留/高级未启用字段”说明中。


### 5.3 认证（Logto）

#### 服务端 JWT 校验
- `LOGTO_ISSUER`：issuer URL。
- `LOGTO_JWKS_URI`：JWKS 地址。
- `LOGTO_AUDIENCE`：API audience。
- `LOGTO_REQUIRED_SCOPES`：空格分隔字符串，如 `openid profile email`。

#### 前端 OAuth 配置
- `LOGTO_ENDPOINT`：Logto 服务地址。
- `LOGTO_APP_ID`：客户端应用 ID。
- `LOGTO_REDIRECT_URI`：登录回调地址。
- `LOGTO_POST_LOGOUT_REDIRECT_URI`：登出回跳地址。

#### 页面要求
- 用户打开登录开关后，所有字段必填。
- 需要提供“测试连接 / 校验 JWKS”的动作。
- 需要提示用户：若未填写 `endpoint` 或 `appId`，前端会自动视为登录不可用。

### 5.4 AI 分析

#### `OPENAI_API_KEY`
- 作用：启用 AI 分析接口。
- 类型：string。
- 范围：非空密钥字符串。

#### `OPENAI_BASE_URL`
- 作用：支持 OpenAI 官方或兼容网关。
- 类型：URL。
- 范围：完整 `http/https` 地址。
- 默认：`https://api.openai.com/v1`。

#### 页面要求
- 将此能力标记为“可跳过”。
- 提供“测试接口可用性”按钮。
- 若未配置，向导完成后系统仍可运行，但 AI 功能置灰或显示未配置状态。

### 5.5 数据源

#### 数据源优先级
- 作用：决定行情获取顺序。
- 类型：数组。
- 范围：`yahoo`、`eodhd`、`database` 的有序组合。
- 默认：`['yahoo', 'database']`。

#### `EODHD_API_KEY`
- 作用：启用 EODHD 行情源。
- 类型：string。
- 范围：非空密钥字符串。
- 页面要求：
  - 若优先级中包含 `eodhd`，建议填写。
  - 若未填写但包含 `eodhd`，需要明确提示“该数据源不会生效”。

### 5.6 实盘 / 模拟盘

#### `LIVE_TRADING_ENABLED`
- 作用：控制 live 模式入口是否可用。
- 类型：boolean。
- 默认：`false`。

#### `DEFAULT_EXCHANGE`
- 作用：默认交易所。
- 类型：enum string。
- 范围：当前配置文件中存在的交易所，如 `binance` / `okx` / `bybit`。
- 默认：`binance`。

#### `DEFAULT_TRADE_MODE`
- 作用：默认交易模式。
- 类型：enum。
- 范围：`paper` / `live`。
- 默认：`paper`。

#### CCXT 凭证组
- Binance：需要 `API_KEY` + `SECRET`。
- OKX：需要 `API_KEY` + `SECRET` + `PASSPHRASE`。
- Bybit：需要 `API_KEY` + `SECRET`。
- 页面要求：
  - 先选择交易所，再选择 `paper/live`，最后展示对应字段。
  - `live` 模式必须二次确认风险。
  - 若 `LIVE_TRADING_ENABLED=false`，隐藏 live 凭证输入区域。

#### `broker_config.json`
建议首版引导页只暴露这些可理解的业务字段：
- `exchanges.<id>.enabled`：boolean。
- `exchanges.<id>.markets`：string[]。
- `exchanges.<id>.default_market`：string。
- `exchanges.<id>.paper_mode.enabled`：boolean。
- `exchanges.<id>.paper_mode.sandbox_url`：URL。
- `exchanges.<id>.paper_mode.initial_balance_usdt`：number，建议 `> 0`。
- `risk_management.position_limits.max_position_size_usd`：number，建议 `> 0`。
- `risk_management.position_limits.max_positions_count`：int，建议 `>= 1`。
- `risk_management.position_limits.max_leverage`：int，建议 `>= 1`。
- `risk_management.loss_limits.max_daily_loss_usd`：number，建议 `>= 0`。
- `risk_management.loss_limits.max_daily_loss_percent`：number，建议 `0-100`。
- `risk_management.loss_limits.max_drawdown_percent`：number，建议 `0-100`。
- `risk_management.order_limits.min_order_size_usd`：number，建议 `> 0`。
- `risk_management.order_limits.max_order_size_usd`：number，建议 `>= min_order_size_usd`。
- `risk_management.order_limits.max_slippage_percent`：number，建议 `0-100`。
- `trading_settings.default_timeframe`：enum，建议来源于 `supported_timeframes`。
- `trading_settings.supported_timeframes`：string[]；当前默认值包括 `1s/1m/5m/15m/30m/1h/4h/1d`。

### 5.7 策略执行与资源控制

#### `strategy_config.json`

1) `strategy.filePath`
- 作用：用户策略目录。
- 类型：string path。
- 默认：`resources/strategy`。

2) `sandbox.*`
- `mode`：enum，`soft` / `subprocess` / `docker`；默认 `subprocess`。
- `timeoutSeconds`：number，建议 `> 0`；默认 `30`。
- `maxMemoryMB`：int，建议 `>= 128`；默认 `512`。
- `maxCpuPercent`：int，建议 `1-100`；默认 `100`。
- `allowNetwork`：boolean；默认 `false`。
- `allowFileWrite`：boolean；默认 `false`。
- `dockerImage`：string；仅 `docker` 模式需要。

3) `workerPool.*`
- `enabled`：boolean；默认 `true`。
- `poolSize`：int，建议 `>= 1`，建议不超过 CPU 核数；默认 `4`。
- `taskTimeoutSeconds`：number，建议 `> 0`；默认 `300`。
- `maxMemoryMB`：int，建议 `>= 256`；默认 `1024`。
- `heartbeatIntervalSeconds`：number，建议 `> 0`；默认 `10`。
- `shutdownTimeoutSeconds`：number，建议 `> 0`；默认 `30`。
- `maxQueueSize`：int，建议 `>= 0`；`0` 代表不限。
- `allowNetwork`：boolean；默认 `true`。
- `allowFileWrite`：boolean；默认 `true`。

页面要求：
- 首版引导页只展示 `strategy.filePath`、`sandbox.mode`、`workerPool.enabled`、`workerPool.poolSize`。
- 其余项放到“高级执行设置”。
- 当 `sandbox.mode=docker` 时才显示 `dockerImage`。

### 5.8 报告与站点信息

#### `REPORT_SHARE_SECRET`
- 作用：生成报告分享 token。
- 类型：string。
- 范围：高强度随机字符串。
- 默认：代码内有弱默认值，仅开发环境可接受。
- 页面要求：若用户开启“公开分享报告”，应强制设置。

#### `REPORT_MAX_AGE_DAYS`
- 类型：int，建议 `>= 1`。
- 默认：`30`。

#### `report_config.json`
- `report.output_directory`：string path。
- `report.default_format`：当前建议 `html`。
- `report.supported_formats`：当前默认 `html/pdf`。
- `export.pdf.page_size`：如 `A4`。
- `export.pdf.orientation`：`portrait/landscape`。
- `export.pdf.margin_mm`：number，建议 `>= 0`。
- `export.pdf.include_watermark`：boolean。
- 注意：当前代码明确使用的是 `output_directory`，其余字段更多是模板/预留能力，可放高级区。

#### `SITE_*`
- `SITE_TITLE`、`SITE_DESCRIPTION`
- `SITE_DOCS_URL`、`SITE_GITHUB_URL`、`SITE_TWITTER_URL`、`SITE_EMAIL`
- `SITE_STATS_STRATEGIES`、`SITE_STATS_BACKTESTS`、`SITE_STATS_USERS`
- 作用：落地页品牌与统计展示。
- 类型：string。
- 页面要求：全部可跳过。

## 6. 哪些一定要配，哪些可以不配

### 6.1 启动级必须有
- 必须明确有一个可用的“数据存储方案”：
  - 默认 SQLite 也可以，但用户必须在向导中确认。
- 必须明确 `ENABLE_LOGIN` 状态。
- 必须生成或填写 `ENCRYPTION_KEY`，否则后续凭证保存能力不可用，不适合作为正式安装完成态。

### 6.2 功能级必须有
- 启用登录时，Logto 全套字段必须完整。
- 启用 AI 时，必须至少有 `OPENAI_API_KEY`。
- 启用 EODHD 时，必须有 `EODHD_API_KEY`。
- 启用实盘时，必须同时满足：
  - `LIVE_TRADING_ENABLED=true`
  - 对应交易所在 `broker_config.json` 中 `enabled=true`
  - 对应交易模式凭证完整
  - 推荐 `DEFAULT_TRADE_MODE=paper` 先完成模拟验证
- 启用跨域登录时，必须配置明确的 CORS origins，不能使用 `*` + credentials。
- 启用报告公开分享时，必须配置 `REPORT_SHARE_SECRET`。

### 6.3 可完全跳过
- OpenAI
- EODHD
- Logto
- 交易所凭证
- 站点品牌信息
- 代理
- 报告高级导出配置
- 日志高级配置

## 7. 推荐配置顺序

### 7.1 推荐向导步骤

#### Step 1：欢迎页 / 安装模式
- 选择部署模式：
  - 本地单机开发
  - 公网部署
- 作用：后续用于决定默认值（如 是否推荐登录）。

#### Step 2：安全基础
- 生成 `ENCRYPTION_KEY`
- 选择 `ENABLE_LOGIN=false/true`
- 若开启登录，仅先展示“后续还要配置 Logto”提醒，不必在此页一次填完

#### Step 3：数据存储
- 选择数据库：SQLite / PostgreSQL
- SQLite：确认文件路径
- PostgreSQL：填写 host/port/database/username/password
- 目标：保证系统有稳定存储落点

#### Step 4：认证（条件步骤）
- 仅当 `ENABLE_LOGIN=true` 时出现
- 填写 Logto 服务端与前端 OAuth 配置
- 校验 JWKS 可访问、redirect URI 格式正确

#### Step 5：数据源（推荐步骤）
- 选择默认数据源优先级
- 如选择 EODHD，填写 `EODHD_API_KEY`
- 不配置 EODHD 时默认 `yahoo -> database`

#### Step 6：AI（可跳过）
- 填写 `OPENAI_API_KEY`
- 可选改写 `OPENAI_BASE_URL`
- 进行连通性测试

#### Step 7：交易（可跳过）
- 是否启用 live trading
- 设置默认交易所与默认模式
- 配置 `broker_config.json` 中的启用交易所与基础风控
- 再填写 paper/live 对应凭证
- 强制先提示“先完成 paper，后开启 live”

#### Step 8：品牌与报告（可跳过）
- 配置 `SITE_*`
- 若开启公开分享，填写 `REPORT_SHARE_SECRET`

#### Step 9：确认与落盘
- 展示：
  - 将写入哪些文件
  - 哪些值为默认值
  - 哪些能力未配置，因此功能不可用
- 用户确认后统一写盘
- 写盘成功后展示“重启服务 / 立即进入系统”建议

### 7.2 不建议的顺序
- 不要先让用户填 OpenAI / 交易所密钥，再填 `ENCRYPTION_KEY`。
- 不要在未确定部署方式前就要求用户配置 CORS。
- 不要在未开启登录前就强迫填写 Logto。
- 不要在未开启实盘前就展示 live key。

## 8. 首次安装引导页的页面信息架构

### 8.1 页面结构
- 左侧：步骤导航（支持完成态、警告态、可跳过态）
- 右侧：当前步骤表单
- 顶部：当前部署模式与安装摘要
- 底部：`上一步` / `下一步` / `跳过` / `保存草稿` / `完成安装`

### 8.2 每一步需要展示的信息
- 本步目标
- 为什么需要这个配置
- 默认值说明
- 生效文件路径
- 是否敏感
- 是否必填
- 不配置会失去哪些功能

### 8.3 校验与提示
- 实时校验：格式、范围、依赖关系
- 提交前校验：跨字段关系，例如：
  - `ENABLE_LOGIN=true` 但 Logto 字段不全
  - `LIVE_TRADING_ENABLED=true` 但未填写 live 凭证
  - `DEFAULT_TRADE_MODE=live` 但 live 被全局禁用
- 敏感项提示：隐藏显示、复制、不回显原文

## 9. 功能需求

### 9.1 必备功能
- 读取现有配置并预填
- 判断哪些能力已可用 / 未可用
- 支持跳过可选步骤
- 支持按条件显示字段
- 支持生成随机密钥
- 支持基础连接测试：
  - Logto JWKS
  - OpenAI
  - 交易所凭证
- 支持统一预览变更并一次性写入

### 9.2 建议功能
- 提供“开发模式推荐值”一键填充
- 提供“生产模式安全检查”清单
- 提供“配置来源”展示：当前值来自文件、默认值还是数据库
- 支持导出安装摘要

### 9.3 非目标
- 首版不处理数据库中的用户个性化设置迁移
- 首版不覆盖所有 `database_config.json` 预留字段
- 首版不做 Docker / Kubernetes 编排自动生成

## 10. 技术约束与实现注意事项

### 10.1 需要特别说明的现状约束
- `database_config.json` 中部分高级字段当前未被实际运行时代码使用，应在 UI 中标记为“预留字段”或暂不暴露。
- `report_config.json` 当前明确被使用的关键字段是 `report.output_directory`，其余字段更多用于模板化扩展。
- `ENABLE_LOGIN` 在不同代码路径上的默认值并不完全一致，因此安装向导必须显式写入该值，不能依赖未配置状态。
- 交易所凭证与 OpenAI 凭证支持后续通过 Settings 页写入数据库，但首次安装仍应以文件初始化为主。

### 10.2 安全要求
- 不将真实密钥写入前端日志。
- 不在 review 页面回显完整 secret。
- 生成的 `ENCRYPTION_KEY` 不应自动上传或外传。
- 实盘步骤必须展示显著风险提示。

## 11. 验收标准

### 11.1 MVP 验收
- 用户仅完成以下配置也能顺利进入系统：
  - `ENCRYPTION_KEY`
  - 明确的登录状态
  - 确认数据库方案（默认 SQLite 可接受）
  - 确认前端 API 访问方案（默认 `/api` 可接受）
- 完成向导后，系统能正常启动并进入首页。
- 所有未配置能力在 UI 中有明确“未启用/未配置”状态，而不是报错。

### 11.2 条件能力验收
- 开启登录后，缺失任一 Logto 必填项不能完成安装。
- 开启 AI 后，OpenAI 测试失败时允许用户返回修改，不允许标记为“已配置成功”。
- 开启实盘后，若缺失任何必要凭证或全局开关未打开，不能完成交易配置步骤。
- 开启跨域凭证后，如果 origins 仍为 `*`，页面必须阻止提交。

## 13. 输出文件建议

建议将引导页最终写入以下文件：
- `backend/.env`
- `frontend/.env`
- `backend/resources/config/database_config.json`
- `backend/resources/config/strategy_config.json`
- `backend/resources/config/broker_config.json`
- 可选：`backend/resources/config/report_config.json`
- 可选：`backend/resources/config/logger_config.json`

## 14. 开发建议

### 14.1 页面开发优先级
- P0：只做“读取现有配置 + 生成/保存基础配置 + 校验依赖关系”
- P1：增加连接测试能力
- P2：增加高级配置折叠区
- P3：增加生产模式安全检查清单

### 14.2 对后续开发最有价值的切分方式
- 先实现“配置模型 + 配置校验器 + 文件读写服务”
- 再实现前端 Step Wizard
- 最后实现 OpenAI / Logto / Binance 的测试动作