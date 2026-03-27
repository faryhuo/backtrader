# config 目录说明

配置与环境管理目录，集中维护后端运行所需的环境变量、默认配置与校验逻辑.

## 功能职责（Functional）
- `settings.py`：读取 `.env`/环境变量并提供默认值（数据库、认证、AI、代理等配置）。
  - **数据库配置**：统一提供 `DATABASE_URL`（优先使用环境变量，否则使用绝对路径 `DEFAULT_DB_URL`），以及 `DEFAULT_DB_PATH`（绝对路径），避免相对路径导致的多数据库文件问题
- `config_manager.py`：运行时配置管理器，支持动态加载与热更新broker 配置
- `sandbox_config.py`：策略沙箱配置（隔离模式/超时/资源限制等），从 `SANDBOX_*` 环境变量加载
- 对资源路径、外部依赖（broker、AI、DB 等）进行配置校验与集中暴露

## 非功能性要求（Non-Functional）
- 安全：禁止在代码库中出现真实密钥/账号；敏感配置必须通过环境变量或外部文件注入�?
- 可维护性：配置项集中在 `settings.py`，避免散落到业务模块.
- 可移植性：默认值需适配本地/容器/生产多环境.

## 约定与规�?
- 新增配置项时同步更新 `backend/.env.template` 与相关文档.
- 配置层只做读取与校验，不承载业务逻辑或 I/O 副作用.


- Runtime defaults now align with the deployed backend layout: SQLite defaults to `trading_sessions.db` under the backend root, and strategies default to `resources/strategy`.

- AI provider settings now support `AI_PROVIDER_PRIORITY` plus provider-specific keys for OpenAI, MiniMax, Gemini, and Claude. Database-backed settings override environment variables.
- AI provider environment fallbacks now include provider-specific runtime model variables such as `OPENAI_MODEL`, `MINIMAX_MODEL`, `GEMINI_MODEL`, and `CLAUDE_MODEL`.
