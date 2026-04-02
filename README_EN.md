# Backtrader Quantitative Trading System

<p align="right">
  <strong>🌐 Language:</strong>
  <a href="README.md">简体中文</a> |
  <a href="README_EN.md">English</a>
</p>

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.124%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3.1-61dafb?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A next-generation AI-powered algorithmic trading platform supporting strategy backtesting, live/paper trading, parameter optimization, and intelligent analysis.

</div>

---

## ✨ Features

### Core Features

- ✅ **Strategy Backtesting System** - Complete backtesting framework based on the Backtrader engine
- ✅ **Live/Paper Trading** - Binance Spot live and paper trading support
- ✅ **Walk-Forward Optimization** - Train/validation set separation with overfitting detection
- ✅ **Online Strategy Editor** - Monaco Editor for writing and debugging strategies online with syntax highlighting
- ✅ **Strategy Sandbox Execution** - Supports subprocess/docker isolation modes to prevent malicious code execution
- ✅ **Multi-language Support** - Chinese/English internationalization (i18n) with complete translation coverage
- ✅ **AI Intelligent Analysis** - OpenAI integration for automatic backtest result analysis and optimization suggestions
- ✅ **WebSocket Real-time Updates** - Real-time trading status, orders, positions, and log updates
- ✅ **Multi-session Management** - Support for running multiple strategies concurrently with independent management
- ✅ **Authentication & Authorization** - Optional Logto JWT authentication integration
- ✅ **Encrypted Credential Storage** - Database credentials encrypted using Fernet with UI configuration support
- ✅ **Portfolio Backtesting** - Support for multi-strategy, multi-asset portfolio backtesting analysis

### Supported Exchanges

#### Supported Exchange
- Binance Spot
- Supports Paper Trading and Live Trading

---

## 📷 Interface Preview

### Main Feature Pages

<table>
  <tr>
    <td align="center">
      <img src="docs/images/homepage.png" width="400" alt="Homepage"/>
      <br/>
      <b>Homepage</b>
    </td>
    <td align="center">
      <img src="docs/images/run_strategy.png" width="400" alt="Run Strategy"/>
      <br/>
      <b>Run Strategy</b>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="docs/images/strategy_maintain.png" width="400" alt="Strategy Management"/>
      <br/>
      <b>Strategy Management</b>
    </td>
    <td align="center">
      <img src="docs/images/backtest_history.png" width="400" alt="Backtest History"/>
      <br/>
      <b>Backtest History</b>
    </td>
  </tr>
  <tr>
    <td align="center" colspan="2">
      <img src="docs/images/portfolio.png" width="400" alt="Portfolio Backtest"/>
      <br/>
      <b>Portfolio Backtest</b>
    </td>
  </tr>
</table>


---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- (Optional) Docker & Docker Compose

### Option 1: One-Click Start (Development Mode)

After cloning the project, use the quick start scripts:

```bash
git clone https://github.com/faryhuo/backtrader.git
cd backtrader
```

**Windows Users:**

```bash
# Full build (install dependencies + build frontend + copy static resources)
build.bat

# Start backend server only (production mode)
start_server.bat
```

**macOS / Linux Users:**

```bash
# Add execute permissions (first time only)
chmod +x *.sh

# Full build (install dependencies + build frontend + copy static resources)
./build.sh

# Start backend server only (production mode)
./start_server.sh
```

### Option 2: Docker Deployment

```bash
git clone https://github.com/faryhuo/backtrader.git
```

```bash
cd backtrader && bash docker-build-optimized.sh

# Run in background
docker-compose up -d
```

Access: `http://localhost:8020`

---

## 👨‍💻 Development Guide

### Environment Setup

1. **Python Virtual Environment** (Recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. **Install Development Dependencies**

```bash
cd backend
pip install -r requirements.txt

cd ../frontend
npm install
```


### Extending Exchange Support

#### Adding a New CCXT Exchange

1. Add credentials in `.env`:
   ```
   CCXT_NEWEXCHANGE_PAPER_API_KEY=xxx
   CCXT_NEWEXCHANGE_PAPER_SECRET=xxx
   ```

2. Add configuration in `broker_config.json`:
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

### Security Documentation

For detailed security architecture, threat models, and deployment recommendations, please refer to **[SECURITY.md](SECURITY.md)**.

### Quick Security Checklist

- [ ] Enable subprocess sandbox mode (`SANDBOX_MODE=subprocess`)
- [ ] Enable authentication (`ENABLE_LOGIN=true`)
- [ ] Configure strict CORS policies
- [ ] Disable sandbox file writing (`SANDBOX_ALLOW_FILE_WRITE=false`)
- [ ] Disable sandbox network access (`SANDBOX_ALLOW_NETWORK=false`)
- [ ] Use HTTPS reverse proxy

### Reporting Security Vulnerabilities

If you discover a security vulnerability, please do not disclose it publicly. Contact the maintainers directly for responsible disclosure.

---

## 🤝 Contributing

We welcome all forms of contributions!

### Contribution Process

1. Fork this repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'feat: add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Submit a Pull Request

### Pull Request Guidelines

- Briefly describe the feature/fix
- Link related Issues (if any)
- Include screenshots for UI changes
- Describe any configuration/migration changes

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Thanks to the following open-source projects:

- [Backtrader](https://www.backtrader.com/) - Powerful backtesting engine
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [React](https://react.dev/) - User interface library
- [CCXT](https://github.com/ccxt/ccxt) - Unified cryptocurrency exchange API
- [Ant Design](https://ant.design/) - Enterprise-grade UI component library

---

## 📞 Contact

- Issue Tracker: [GitHub Issues](../../issues)
- Discussions: [GitHub Discussions](../../discussions)

---

<div align="center">

**⭐ If this project helps you, please give us a Star! ⭐**

</div>
