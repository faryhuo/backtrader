# 首次安装引导页 FRS

## 1. 文档目标

本文档定义“首次安装引导页（First-Run Setup Wizard）”的需求范围与验收标准。目标是让用户在第一次启动系统时，完成最小可用配置，并按需开启认证、AI、多数据源与 Binance 交易能力。

本版 FRS 以当前代码为准，明确以下边界：

- AI 不是单一 OpenAI，而是统一 AI provider 模型，支持 `openai`、`minimax`、`gemini`、`claude`
- Trading 首装页只支持 `binance`
- Trading 页面需要同时配置 `paper` 与 `live` 两套凭证
- 首装页不配置 `VITE_API_BASE_URL`
- 首装页不修改 `frontend/.env`
- Database 步骤不配置 `DATABASE_URL`，只配置 `database_config.json`

## 2. 设计目标

### 2.1 核心目标

- 让用户在不了解项目内部结构的情况下完成首次可运行配置
- 让“必须配置项”和“可选增强项”清晰分层
- 在不写入数据库的前提下完成启动期 bootstrap
- 对敏感配置提供隐藏显示、掩码回显与风险提示

### 2.2 设计原则

- 最小可用优先：先保证应用能启动、能保存配置、能访问基础功能
- 条件暴露：只有用户开启某个能力时，才显示对应字段
- 文件初始化优先：首装阶段以 `.env` 和 `resources/config/*.json` 为主，不直接写数据库
- 安全默认：默认关闭登录、默认关闭 live、默认不强制 AI、默认不公开报告

## 3. 配置来源与写入目标

### 3.1 首装页读取来源

- `backend/.env`，不存在时回退 `backend/.env.template`
- `backend/resources/config/database_config.json`
- `backend/resources/config/strategy_config.json`
- `backend/resources/config/broker_config.json`
- `backend/resources/config/report_config.json`
- `backend/resources/config/logger_config.json`

### 3.2 首装页写入目标

首装页最终只写入以下文件：

- `backend/.env`
- `backend/resources/config/database_config.json`
- `backend/resources/config/strategy_config.json`
- `backend/resources/config/broker_config.json`
- `backend/resources/config/report_config.json`
- `backend/resources/config/logger_config.json`

### 3.3 明确不写入的目标

- 不写 `frontend/.env`
- 不写 `VITE_API_BASE_URL`
- 不写数据库中的用户设置、AI provider 设置或交易凭证

## 4. 配置项范围

### 4.1 P0：首次启动建议必须完成

| 配置项 | 写入位置 | 级别 | 说明 |
|---|---|---|---|
| `ENCRYPTION_KEY` | `backend/.env` | 强必填 | 用于加密保存 API Key、交易凭证等敏感值 |
| `ENABLE_LOGIN` | `backend/.env` | 必填 | 明确登录是否启用 |
| `database.type` | `database_config.json` | 必填 | `sqlite` 或 `postgresql` |
| `database.sqlite.path` 或 PostgreSQL 结构化字段 | `database_config.json` | 条件必填 | 根据数据库模式填写 |

### 4.2 P1：按功能开启时必须完成

| 配置组 | 写入位置 | 何时必填 | 说明 |
|---|---|---|---|
| Logto 认证组 | `backend/.env` | 开启登录时 | 服务端 JWT 校验 + 前端 OAuth 所需参数 |
| AI provider 组 | `backend/.env` | 开启 AI 时 | 多 provider 优先级与各 provider API Key / Base URL |
| EODHD 数据源 | `backend/.env` | 选择 EODHD 时 | 需要 `EODHD_API_KEY` |
| Binance live 组 | `backend/.env` + `broker_config.json` | 开启 live 时 | `LIVE_TRADING_ENABLED` + Binance live 凭证 + 风险确认 |
| 报告公开分享组 | `backend/.env` | 开启公开分享时 | `REPORT_SHARE_SECRET` 必填 |

### 4.3 P2：可选增强配置

- `HTTP_PROXY`
- `HTTPS_PROXY`
- `CORS_ALLOW_ORIGINS`
- `CORS_ALLOW_ORIGIN_REGEX`
- `CORS_ALLOW_CREDENTIALS`
- `strategy_config.json` 中的策略目录、沙箱模式、worker pool 基础项
- `SITE_*` 品牌字段
- `report.output_directory`

## 5. AI 需求

### 5.1 能力范围

当前实现中的 AI 模块已经是统一 provider 模型，而不是单一 OpenAI 通道。首装页必须反映这一点：

- 支持 provider：`openai`、`minimax`、`gemini`、`claude`
- 支持 provider priority fallback
- 支持文本分析与多模态调用
- 对不支持图片输入的模型，运行时会自动降级为纯文本请求

### 5.2 配置项

| 配置项 | 写入位置 | 说明 |
|---|---|---|
| `AI_PROVIDER_PRIORITY` | `backend/.env` | 启用 provider 的优先级顺序，逗号分隔 |
| `AI_PROVIDER` | `backend/.env` | 与第一优先 provider 保持一致，用于兼容旧逻辑 |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | `backend/.env` | OpenAI provider |
| `MINIMAX_API_KEY` / `MINIMAX_BASE_URL` | `backend/.env` | MiniMax provider |
| `GEMINI_API_KEY` / `GEMINI_BASE_URL` | `backend/.env` | Gemini provider |
| `CLAUDE_API_KEY` / `CLAUDE_BASE_URL` | `backend/.env` | Claude provider |

### 5.3 页面要求

- AI 步骤必须支持启用一个或多个 provider
- provider 顺序必须可调整，用于表示 fallback 顺序
- 每个 provider 独立配置 `API key` 与 `Base URL`
- provider 必须支持单独测试
- 首装页不强制配置默认模型名
- 页面需要提示：默认模型名可在后续 Settings 页继续配置

### 5.4 校验规则

- AI 步骤允许整体跳过
- 若开启 AI，至少启用 1 个 provider
- 对所有已启用 provider，`API key` 必填
- `Base URL` 为空时应回退到代码默认值

## 6. Database 需求

### 6.1 模式范围

首装页 Database 步骤只支持两种模式：

- `sqlite`
- `postgresql`

### 6.2 非目标

本版向导不暴露以下内容：

- `DATABASE_URL`
- 任意 SQLAlchemy URL 直填模式
- `frontend/.env` 中的任何地址类配置

### 6.3 页面要求

- SQLite 模式下只要求确认 `sqlite.path`
- PostgreSQL 模式下使用结构化表单输入 `host/port/database/username/password`
- 页面需要明确提示：数据库模式将写入 `backend/resources/config/database_config.json`

## 7. Trading 需求

### 7.1 范围收敛

首装页 Trading 步骤只支持 `binance`，不再暴露 `okx`、`bybit` 或其他交易所。

### 7.2 配置项

| 配置项 | 写入位置 | 说明 |
|---|---|---|
| `LIVE_TRADING_ENABLED` | `backend/.env` | live 总开关 |
| `DEFAULT_EXCHANGE=binance` | `backend/.env` | 固定为 Binance |
| `DEFAULT_TRADE_MODE` | `backend/.env` | `paper` / `live` |
| `CCXT_BINANCE_PAPER_API_KEY` / `SECRET` | `backend/.env` | Binance 测试网凭证 |
| `CCXT_BINANCE_LIVE_API_KEY` / `SECRET` | `backend/.env` | Binance 实盘凭证 |
| `broker_config.json` 中的 binance 节点 | `broker_config.json` | 交易所启用、paper sandbox、基础风险限制 |

### 7.3 页面要求

- 页面只展示 Binance
- 页面需要以 `paper` / `live` 两个 Tab 展示两套 guide 与配置区域
- 每个 Tab 都需要包含各自模式的 guide、凭证配置和测试动作
- 页面可以选择默认模式，但不能因为默认模式切换而移除另一种模式的配置能力
- `paper` 和 `live` 都应支持单独测试
- `paper` Tab 必须展示 Binance Spot Test Network 的官方引导与 sandbox 配置说明
- `live` Tab 必须展示 Binance API Management 的官方引导、权限说明和 IP 限制说明
- `live` 风险确认必须显式勾选
- `broker_config.json` 最终应只保留 Binance 交易所配置

### 7.4 校验规则

- 若只填写一半 paper 凭证，阻止进入下一步
- 若只填写一半 live 凭证，阻止进入下一步
- 若开启 `LIVE_TRADING_ENABLED=true`，live 凭证必须完整
- 若默认模式是 `live`，必须先开启 `LIVE_TRADING_ENABLED`

## 8. 页面步骤

### 8.1 推荐步骤

1. Welcome
2. Security
3. Database
4. Authentication（仅 `ENABLE_LOGIN=true` 时出现）
5. Data Source
6. AI
7. Trading
8. Brand & Report
9. Review

### 8.2 每一步展示内容

- 本步目标
- 作用说明
- 默认值说明
- 写入文件路径
- 是否敏感
- 不配置的影响

## 9. 页面交互要求

### 9.1 必备功能

- 读取现有配置并预填
- 掩码回显敏感值
- 一键生成 `ENCRYPTION_KEY`
- 条件显示字段
- AI provider 单独测试
- Binance paper/live 单独测试
- Binance 交易配置区域必须采用 `paper` / `live` Tab，分别提供各自的官方 guide 和模式配置
- Logto JWKS 测试
- 最终 review 中优先展示配置改动摘要，让用户理解“改了什么”；文件写入目标只作为次级信息

### 9.2 非目标

- 不做数据库迁移
- 不生成 Docker / Kubernetes 配置
- 不写入 Settings 数据库表
- 不管理 `frontend/.env`

## 10. 验收标准

### 10.1 MVP 验收

- 用户只配置以下内容也能完成首装：
  - `ENCRYPTION_KEY`
  - `ENABLE_LOGIN`
  - `database_config.json` 中的数据库模式
- 完成向导后，系统能正常启动并进入首页
- 向导 review 页应按配置分组展示改动摘要，而不是只展示后端 bootstrap 文件列表

### 10.2 AI 验收

- AI 步骤能配置多个 provider
- provider 顺序调整后能正确写入 `AI_PROVIDER_PRIORITY`
- 第一优先 provider 会同步写入 `AI_PROVIDER`
- 未配置任何 provider key 时，AI 仍可跳过，系统其他功能不受阻塞

### 10.3 Trading 验收

- Trading 步骤只展示 Binance
- paper/live 两套配置通过 Tab 切换，但都可独立编辑和保存
- paper Tab 可直接打开 Binance Spot Test Network 并看到 sandbox 配置说明
- live Tab 可直接打开 Binance API Management，并看到权限和 IP 限制说明
- 开启 live 时若未填 live key 或未勾选风险确认，不能完成安装
- 保存后旧的 OKX / Bybit bootstrap 凭证应被清空或不再参与引导配置

### 10.4 Database 验收

- 向导中不出现 `DATABASE_URL` 输入项
- 保存后数据库模式只通过 `database_config.json` 生效

## 11. 实现说明

### 11.1 后端接口

- `GET /api/setup/wizard`
- `PUT /api/setup/wizard`
- `POST /api/setup/wizard/test`

### 11.2 前端页面

- 路由：`/onboarding`
- 页面：`frontend/src/pages/OnboardingSetup.jsx`
- 服务：`frontend/src/services/setupApi.js`

### 11.3 后端服务

- `backend/src/service/setup_wizard_service.py`

该服务负责：

- 读取现有 bootstrap 配置
- 组装前端表单数据
- 处理掩码 secret 回写
- 写入 `.env` 与 JSON 配置文件
- 统一处理 Logto / AI / Binance / Proxy 测试
