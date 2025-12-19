# backend/ 目录说明

本目录为后端服务（FastAPI + Backtrader 引擎 + SQLAlchemy 持久化 + 交易适配器），并包含运行时资源（策略脚本、图片、前端构建产物等）。

---

## 入口文件

- `backend/main.py`：服务启动入口（使用 `daphne` 运行 ASGI 应用），读取 `HOST/PORT/LOG_LEVEL` 等环境变量。
- `backend/api.py`：导出 `app`（供 ASGI 服务器或其他集成方式引用）。

---

## 主要目录

- `backend/src/`：后端核心源码（分层组织，细节见 `backend/src/src.md`）
  - `backend/src/routes/`：HTTP/WebSocket 路由层（参数校验、响应编排；见 `backend/src/routes/routes.md`）
  - `backend/src/service/`：业务编排与引擎层（回测、实盘会话、策略沙箱、WebSocket 管理等；见 `backend/src/service/service.md`）
  - `backend/src/db/`：数据库模型与存储封装（会话/回测/设置/凭证等；见 `backend/src/db/db.md`）
  - `backend/src/brokers/`：交易适配器层（如 CCXT、IBKR；见 `backend/src/brokers/brokers.md`）
  - `backend/src/config/`：配置与配置管理（环境变量、DB 优先的配置管理等；见 `backend/src/config/config.md`）
  - `backend/src/utils/`：工具函数（鉴权、加密、配置加载等；见 `backend/src/utils/utils.md`）

- `backend/resources/`：运行时资源目录（程序运行时会读写此处）
  - `backend/resources/strategy/`：用户策略脚本（`*.py`）与模板（见 `backend/resources/strategy/strategy.md`）
  - `backend/resources/config/`：运行时配置（如 `broker_config.json`）
  - `backend/resources/images/`：回测/分析生成的图片等
  - `backend/resources/frontend/`：前端构建产物拷贝（由构建脚本生成，用于后端静态托管）

- `backend/tests/`：pytest 测试用例（单元测试为主，覆盖 config/db/service/utils/brokers 等）。

---

## 依赖与脚本

- `backend/requirements.txt`：后端运行依赖。
- `backend/requirements-dev.txt`：后端开发/测试依赖。
- `backend/run_tests_coverage.bat`：在 Windows 下运行测试与覆盖率的脚本（如有）。

---

## 环境变量与配置文件

- `backend/.env`：本地运行环境变量（不应提交到仓库）。
- `backend/.env.template`：环境变量模板（新增配置项时需同步更新）。

常见变量示例：
- `DATABASE_URL`：数据库连接（默认通常为 SQLite）。
- `OPENAI_API_KEY` / `OPENAI_BASE_URL`：AI 分析相关配置（也可由设置页面写入 DB）。
- `LOGTO_*` / `ENABLE_LOGIN`：可选的登录认证配置。
- `LIVE_TRADING_ENABLED`：是否启用实盘/模拟盘相关接口。

---

## 本地数据库与缓存（生成文件）

以下文件通常是运行时生成的，不建议提交到仓库：
- `backend/trading_sessions.db`：本地 SQLite 数据库文件（会话/设置/凭证等持久化）。
- `backend/trading_sessions.db-wal`、`backend/trading_sessions.db-shm`：SQLite 在 WAL 模式下生成的日志/共享内存文件。
- `backend/__pycache__/`、`backend/.pytest_cache/`：Python/pytest 缓存目录。

