# Backtrader 量化交易系统

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.124%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3.1-61dafb?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

新一代 AI 驱动的算法交易平台，支持策略回测、实盘/模拟交易、参数优化与智能分析。

[功能特性](#功能特性) • [快速开始](#快速开始) • [使用文档](#使用文档) • [架构设计](#架构设计) • [开发指南](#开发指南)

</div>

---

## 📋 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [部署方式](#部署方式)
- [使用文档](#使用文档)
- [架构设计](#架构设计)
- [开发指南](#开发指南)
- [故障排查](#故障排查)
- [安全性](#安全性)
- [贡献指南](#贡献指南)
- [许可协议](#许可协议)

---

## ✨ 功能特性

### 核心功能

- ✅ **策略回测系统** - 基于 Backtrader 引擎的完整回测框架
- ✅ **实盘/模拟交易** - CCXT（加密货币）和 IBKR（传统证券）适配器支持
- ✅ **Walk-Forward 参数优化** - 训练/验证集分离，过拟合检测
- ✅ **在线策略编辑器** - Monaco Editor 在线编写和调试策略代码，支持语法高亮
- ✅ **策略沙箱安全执行** - 支持 subprocess/docker 隔离模式，防止恶意代码执行
- ✅ **多语言支持** - 中文/英文国际化 (i18n)，完整的翻译覆盖
- ✅ **AI 智能分析** - OpenAI 集成，自动分析回测结果并提供优化建议
- ✅ **WebSocket 实时推送** - 交易状态、订单、持仓、日志实时更新
- ✅ **多会话管理** - 支持多个策略并发运行，独立管理
- ✅ **认证授权** - 可选的 Logto JWT 认证集成
- ✅ **凭证加密存储** - 数据库凭证使用 Fernet 加密，支持 UI 配置
- ✅ **组合回测** - 支持多策略、多品种组合回测分析

### 支持的交易所

#### 加密货币（CCXT）
- Binance（币安）
- OKX（欧易）
- Bybit

#### 传统证券（IBKR）
- Interactive Brokers（盈透证券）
- 支持纸盘（Paper Trading）和实盘（Live Trading）

---

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI 0.124.4+ (异步 Web 框架)
- **回测引擎**: Backtrader 1.9.78.123+
- **数据库**: SQLAlchemy 2.0.45+ (支持 SQLite/PostgreSQL)
- **服务器**: Daphne 4.2.1+ (ASGI 服务器，支持 WebSocket)
- **数据源**: yfinance 0.2.66+, CCXT 4.5.28+
- **AI 分析**: OpenAI 2.11.0+
- **交易接口**: CCXT 4.5.28+, IB API 9.81.1+
- **认证**: python-jose 3.3.0+ (JWT)

### 前端
- **框架**: React 18.3.1
- **构建工具**: Vite 6.0.5
- **UI 组件**: Ant Design 6.1.0
- **代码编辑器**: Monaco Editor 0.52.0
- **图表**: Lightweight Charts 4.2.2
- **国际化**: i18next 25.7.2
- **路由**: React Router 7.10.1
- **认证**: Logto React 4.0.9
- **其他**: react-markdown 10.1.0, html2canvas 1.4.1, xlsx 0.18.5

### DevOps & 开发工具
- **容器化**: Docker + Docker Compose 3.9
- **Python 版本**: 3.11+
- **Node 版本**: 18+ (推荐 20+)
- **包管理**: pip (Python), npm (Node.js)
- **代码检查**: ESLint 9.17.0 (前端)
- **测试框架**: pytest (后端)

---

## 🚀 快速开始

### 前置要求

- Python 3.11 或更高版本
- Node.js 18 或更高版本
- (可选) Docker & Docker Compose

### 方式一：本地开发环境

#### 1. 克隆仓库

```bash
git clone <repository-url>
cd backtrader
```

#### 2. 后端设置

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.template .env
# 编辑 .env 文件，填入必要的配置

# 启动后端服务（默认端口 8000）
python main.py
```

#### 3. 前端设置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器（默认端口 5173）
npm run dev
```

#### 4. 访问应用

打开浏览器访问：`http://localhost:5173`

### 方式二：一键启动（开发模式）

Windows 用户可以使用批处理脚本快速启动：

```bash
# 完整构建（安装依赖 + 构建前端 + 复制静态资源）
build.bat

# 开发模式（同时启动后端和前端开发服务器）
start_dev.bat
```

### 方式三：Docker 部署

```bash
# 构建并启动容器（默认端口 8020）
docker-compose up --build

# 后台运行
docker-compose up -d
```

访问：`http://localhost:8020`

---

## 📦 部署方式

### 生产环境部署

#### 1. 使用完整构建脚本

```bash
# Windows
build.bat

# Linux/Mac
chmod +x docker-build-optimized.sh
./docker-build-optimized.sh
```

### 2. 配置生产环境变量

编辑 `backend/.env`（首次使用请从 `.env.template` 复制）：

```env
# ============================================================================
# 加密密钥（必需）
# ============================================================================
# 用于加密数据库中的敏感凭证（API Key、Secret 等）
# 生成方法：python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=your-generated-encryption-key

# ============================================================================
# 数据库配置
# ============================================================================
DATABASE_URL=sqlite:///./trading_sessions.db

# ============================================================================
# 认证配置（可选）
# ============================================================================
ENABLE_LOGIN=false
LOGTO_ISSUER=https://your-logto-domain
LOGTO_JWKS_URI=https://your-logto-domain/oidc/jwks

# ============================================================================
# OpenAI 配置（可选）
# ============================================================================
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1

# ============================================================================
# 策略沙箱安全配置
# ============================================================================
# 沙箱模式：soft（不隔离）、subprocess（进程隔离，推荐）、docker（容器隔离）
SANDBOX_MODE=subprocess
SANDBOX_TIMEOUT_SECONDS=30.0
SANDBOX_MAX_MEMORY_MB=512
SANDBOX_ALLOW_NETWORK=false
SANDBOX_ALLOW_FILE_WRITE=false

# ============================================================================
# 交易所凭证（根据需要配置）
# ============================================================================
# CCXT 格式: CCXT_{交易所}_{模式}_API_KEY/SECRET
CCXT_BINANCE_PAPER_API_KEY=
CCXT_BINANCE_PAPER_SECRET=
CCXT_BINANCE_LIVE_API_KEY=
CCXT_BINANCE_LIVE_SECRET=

# ============================================================================
# IBKR 配置
# ============================================================================
IBKR_PAPER_HOST=127.0.0.1
IBKR_PAPER_PORT=4002
IBKR_LIVE_HOST=127.0.0.1
IBKR_LIVE_PORT=4001
```

**重要安全提示**：
1. **必须设置 `ENCRYPTION_KEY`**：用于加密存储在数据库中的交易所 API 凭证
2. **不要提交 `.env` 文件到版本控制**：`.env` 文件已在 `.gitignore` 中
3. **凭证可通过 UI 配置**：在"设置"页面配置的凭证会加密后存储在数据库中，优先级高于 `.env`
4. **建议使用 subprocess 沙箱模式**：防止不受信任的策略代码执行危险操作

#### 3. 配置交易所参数

编辑 `backend/resources/config/broker_config.json`：

```json
{
  "binance": {
    "adapter": "ccxt",
    "exchange_id": "binance",
    "risk_limits": {
      "max_position_pct": 0.3,
      "max_trade_qty": 1000
    }
  },
  "ibkr": {
    "adapter": "ibkr",
    "risk_limits": {
      "max_position_pct": 0.5,
      "max_trade_qty": 100
    }
  }
}
```

---

## 📖 使用文档

### 策略开发

策略文件存放在 `backend/resources/strategy/` 目录，使用 Backtrader 语法编写：

```python
import backtrader as bt

class MyStrategy(bt.Strategy):
    params = (
        ('period', 20),
    )
    
    def __init__(self):
        self.sma = bt.indicators.SMA(self.data.close, period=self.params.period)
    
    def next(self):
        if not self.position:
            if self.data.close > self.sma:
                self.buy(size=1)
        else:
            if self.data.close < self.sma:
                self.sell(size=1)
```

### 内置策略模板

系统提供了多个经典策略模板：

- `sma_cross.py` - 双均线交叉策略
- `rsi_reversion.py` - RSI 均值回归策略
- `breakout.py` - 突破策略
- `buy_and_hold.py` - 买入持有策略

### 回测执行

1. 进入"运行策略"页面
2. 配置回测参数：
   - 选择策略文件
   - 设置股票代码/交易对
   - 配置起止时间
   - 设置初始资金和手续费
3. 点击"运行回测"
4. 查看结果（收益曲线、夏普比率、最大回撤等）

### 实盘交易

1. 配置交易所凭证（`.env` 文件）
2. 配置 `broker_config.json` 风控参数
3. 进入"实盘交易"页面
4. 创建交易会话：
   - 选择交易所和模式（Paper/Live）
   - 选择策略和交易对
   - 设置资金和参数
5. 启动会话并监控实时状态

### Walk-Forward 优化

1. 进入"参数优化"页面
2. 配置优化参数：
   - 训练集周期
   - 验证集周期
   - 步进窗口
   - 参数范围
3. 运行优化并查看结果
4. 识别过拟合风险

---

## 🏗️ 架构设计

### 项目结构

```
backtrader/
├── backend/                    # Python 后端
│   ├── src/
│   │   ├── routes/            # FastAPI 路由
│   │   │   ├── api_routes.py      # 回测、策略、数据管理
│   │   │   ├── live_routes.py     # 实盘交易 API
│   │   │   ├── ai_routes.py       # AI 分析
│   │   │   ├── websocket_routes.py # WebSocket
│   │   │   └── settings_routes.py # 用户设置
│   │   ├── service/           # 业务逻辑
│   │   │   ├── backtest_engine.py # 回测引擎
│   │   │   ├── live_engine.py     # 实盘引擎
│   │   │   ├── session_manager.py # 会话管理
│   │   │   ├── walkforward_optimizer.py # 参数优化
│   │   │   ├── strategy_sandbox.py # 策略沙箱
│   │   │   └── websocket_manager.py # WebSocket 管理
│   │   ├── brokers/           # 交易所适配器
│   │   │   ├── ccxt_adapter/      # CCXT 加密货币
│   │   │   └── ibkr_adapter/      # IBKR 传统证券
│   │   ├── db/                # 数据库层
│   │   │   ├── models.py          # 数据模型
│   │   │   ├── backtest_storage.py # 回测历史
│   │   │   ├── session_storage.py  # 会话持久化
│   │   │   └── datasource.py      # 数据源
│   │   ├── config/            # 配置管理
│   │   └── utils/             # 工具模块
│   ├── resources/
│   │   ├── strategy/          # 策略文件 (.py)
│   │   ├── config/            # 配置文件
│   │   ├── images/            # 回测图表
│   │   └── frontend/          # 构建后的前端资源
│   ├── main.py                # 入口文件
│   ├── api.py                 # FastAPI 应用导出
│   └── requirements.txt       # Python 依赖
│
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/        # React 组件
│   │   │   ├── Auth/              # 认证组件
│   │   │   ├── Layout/            # 布局和导航
│   │   │   ├── RunStrategy/       # 回测执行
│   │   │   ├── LiveTrading/       # 实盘交易仪表板
│   │   │   ├── StrategyMaintain/  # 策略编辑器
│   │   │   └── WalkForward/       # 参数优化
│   │   ├── pages/             # 页面组件
│   │   ├── services/          # API 客户端
│   │   ├── providers/         # React Context
│   │   ├── hooks/             # 自定义 Hooks
│   │   ├── locales/           # 国际化翻译
│   │   └── config/            # 前端配置
│   ├── package.json
│   └── vite.config.js
│
├── auto_test/                  # 自动化测试
├── docker-compose.yml          # Docker 编排
├── Dockerfile                  # Docker 镜像
├── build.bat                   # Windows 构建脚本
└── start_dev.bat               # Windows 开发启动脚本
```

### 数据流

#### 回测流程

```
前端 → POST /api/backtest → backtest_engine.py
  → 加载策略（strategy_sandbox.py）
  → 获取数据（datasource.py/yfinance）
  → 运行 Backtrader Cerebro
  → 生成图表（resources/images/）
  → 存储结果（backtest_storage.py）
  → 返回指标 + 图表 URL
```

#### 实盘交易流程

```
前端 → POST /api/live/start → live_engine.py
  → SessionManager 创建会话
  → 加载 CCXT/IBKR Store
  → 启动后台线程运行 Cerebro
  → WebSocket 推送实时更新
  → 订单/持仓持久化到数据库
```

### 关键设计模式

- **单例模式**: SessionManager, WebSocketManager
- **适配器模式**: CCXTAdapter, IBKRAdapter 统一接口
- **沙箱模式**: StrategySandbox 安全执行用户代码（支持 subprocess/docker 隔离）
- **观察者模式**: WebSocket 事件广播
- **工厂模式**: 动态加载策略类
- **存储库模式**: 各类 Storage 封装数据访问

---

## 👨‍💻 开发指南

### 环境搭建

1. **Python 虚拟环境**（推荐）

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. **安装开发依赖**

```bash
cd backend
pip install -r requirements.txt

cd ../frontend
npm install
```

### 代码规范

#### Python (PEP 8)
- 使用 4 空格缩进
- 函数/变量使用 `snake_case`
- 类名使用 `PascalCase`
- 添加类型注解（Type Hints）
- API 验证在 `routes/`，业务逻辑在 `service/`

#### JavaScript/React
- 使用 2 空格缩进
- 函数组件优先，使用 Hooks
- 组件名使用 `PascalCase`
- 文件名与组件名一致

#### 提交规范（Conventional Commits）

```
feat: 添加新功能
fix: 修复 Bug
chore: 构建/工具链更新
docs: 文档更新
style: 代码格式（不影响功能）
refactor: 重构
test: 测试相关
```

### 测试

```bash
# 后端测试（带覆盖率报告）
cd backend
python -m pytest --cov=src --cov-report=html:coverage_html --cov-report=xml:coverage.xml

# 或使用批处理脚本 (Windows)
run_tests_coverage.bat

# 前端 Lint
cd frontend
npm run lint
```

### 持续集成 (CI)

项目使用 GitHub Actions 自动运行测试和代码检查。配置文件位于 `.github/workflows/ci.yml`。

| 作业 | 环境 | 检查内容 |
|------|------|----------|
| `backend-tests` | Python 3.11 | pytest 测试 + 覆盖率报告 |
| `frontend-lint` | Node.js 20 | ESLint 代码检查 |

**触发条件**：
- Push 到 `main`/`master` 分支
- 所有 Pull Request

**查看 CI 状态**：
- 在 Pull Request 页面查看检查结果
- GitHub Actions 标签页查看详细日志
- 如需启用 CI Badge，请在 GitHub Actions 中配置工作流后，替换 README 顶部的 CI badge URL

### 添加新策略

1. 在 `backend/resources/strategy/` 创建新文件
2. 继承 `bt.Strategy` 编写策略逻辑
3. 文件名使用 `snake_case.py`
4. 在前端"策略维护"页面即可看到新策略

### 扩展交易所支持

#### 添加新 CCXT 交易所

1. 在 `.env` 添加凭证：
   ```
   CCXT_NEWEXCHANGE_PAPER_API_KEY=xxx
   CCXT_NEWEXCHANGE_PAPER_SECRET=xxx
   ```

2. 在 `broker_config.json` 添加配置：
   ```json
   {
     "newexchange": {
       "adapter": "ccxt",
       "exchange_id": "newexchange",
       "risk_limits": {...}
     }
   }
   ```

---

## 🔧 故障排查

### 常见问题

#### 1. `pycares` 导入错误（已修复）

**问题**：
```
ImportError: cannot import name 'ares_query_a_result' from 'pycares'
```

**原因**：`pycares 5.0.0` 与 `aiodns` 不兼容

**解决**：
项目已在 `requirements.txt` 中设置了版本约束：
```bash
pycares<5.0.0
aiodns>=3.6.1
```
重新安装依赖即可：
```bash
cd backend
pip install -r requirements.txt
```

#### 2. IBKR 连接失败

**问题**：无法连接到 Interactive Brokers Gateway

**检查**：
- IB Gateway/TWS 是否运行（Paper Trading: 端口 4002，Live: 端口 4001）
- `.env` 文件中 `IBKR_*_HOST/PORT` 配置是否正确
- 防火墙是否允许连接
- Client ID 是否唯一（默认使用 123）
- API 连接权限是否在 Gateway 中启用

**解决**：
1. 启动 IB Gateway 并登录
2. 在 Gateway 设置中启用 "Enable ActiveX and Socket Clients"
3. 确认 Socket Port 与 `.env` 配置一致
4. 检查 "Read-Only API" 是否根据需求正确配置

#### 3. WebSocket 连接断开

**问题**：前端实时更新中断

**检查**：
- 后端日志查看 WebSocket 错误
- 浏览器控制台检查网络连接
- 确认 Daphne 服务器正常运行

#### 4. 策略加载失败

**问题**：策略文件无法加载或执行报错

**检查**：
- 策略文件语法是否正确
- 是否继承 `bt.Strategy`
- `__init__` 和 `next` 方法是否实现
- 查看 `strategy_sandbox.py` 日志

### 查看日志

```bash
# 后端日志
cd backend
python main.py  # 控制台输出详细日志

# Docker 日志
docker-compose logs -f
```

---

## 🔐 安全性

> ⚠️ **重要提示**：当前的策略沙箱设计主要面向**受信任环境**。如需部署在多租户或公网环境，请仔细阅读安全文档。

### 安全文档

详细的安全架构、威胁模型和部署建议，请参阅 **[SECURITY.md](SECURITY.md)**。

### 快速安全检查清单

- [ ] 启用 subprocess 沙箱模式 (`SANDBOX_MODE=subprocess`)
- [ ] 启用认证 (`ENABLE_LOGIN=true`)
- [ ] 配置严格的 CORS 策略
- [ ] 禁止沙箱文件写入 (`SANDBOX_ALLOW_FILE_WRITE=false`)
- [ ] 禁止沙箱网络访问 (`SANDBOX_ALLOW_NETWORK=false`)
- [ ] 使用 HTTPS 反向代理

### 报告安全漏洞

如发现安全漏洞，请勿公开披露，直接联系维护者进行负责任的披露。

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 贡献流程

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'feat: add amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

### Pull Request 规范

- 简要描述功能/修复
- 关联相关 Issue（如有）
- UI 更改需附带截图
- 说明配置/迁移变更

---

## 📄 许可协议

本项目采用 MIT 许可协议。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

感谢以下开源项目：

- [Backtrader](https://www.backtrader.com/) - 强大的回测引擎
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化 Web 框架
- [React](https://react.dev/) - 用户界面库
- [CCXT](https://github.com/ccxt/ccxt) - 加密货币交易所统一 API
- [Ant Design](https://ant.design/) - 企业级 UI 组件库

---

## 📞 联系方式

- Issue Tracker: [GitHub Issues](../../issues)
- 讨论区: [GitHub Discussions](../../discussions)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个 Star！⭐**

</div>
