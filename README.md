# Backtrader 量化交易系统

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.124%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3.1-61dafb?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

新一代 AI 驱动的算法交易平台，支持策略回测、实盘/模拟交易、参数优化与智能分析。

</div>

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
