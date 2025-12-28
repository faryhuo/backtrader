# Backtrader 量化交易平台用户指南

## 目录

- [平台概述](#平台概述)
- [快速开始](#快速开始)
- [功能模块](#功能模块)
  - [策略开发与维护](#1-策略开发与维护)
  - [单资产回测](#2-单资产回测)
  - [投资组合回测](#3-投资组合回测)
  - [走向前优化](#4-走向前优化)
  - [回测历史](#5-回测历史)
  - [实盘交易](#6-实盘交易)
  - [报告中心](#7-报告中心)
  - [数据管理](#8-数据管理)
  - [任务中心](#9-任务中心)
  - [系统设置](#10-系统设置)
- [高级功能](#高级功能)
  - [深度分析详解](#11-深度分析详解)
  - [PyFolio 导出与分析](#12-pyfolio-导出与分析)
  - [投资组合优化算法](#13-投资组合优化算法)
  - [再平衡策略配置](#14-再平衡策略配置)
  - [单资产参数定制](#15-单资产参数定制)
- [策略编写指南](#策略编写指南)
- [更多策略示例](#更多策略示例)
- [最佳实践](#最佳实践)
- [性能优化](#性能优化)
- [部署指南](#部署指南)
- [常见问题](#常见问题)
- [术语表](#术语表)
- [附录](#附录)

---

## 平台概述

本平台是一个基于 **Backtrader** 的全功能量化交易系统，提供从策略开发、回测验证到实盘交易的完整解决方案。

### 核心特性

| 特性 | 说明 |
|------|------|
| **策略回测** | 支持单资产和多资产投资组合回测 |
| **参数优化** | 走向前优化（Walk-Forward）防止过拟合 |
| **实盘交易** | 支持 CCXT（加密货币）和 IBKR（传统证券）|
| **AI 分析** | 集成 OpenAI，提供智能策略分析 |
| **深度分析** | 收益热力图、滚动指标、回撤分析 |
| **报告生成** | 生成专业回测报告并支持分享 |
| **多语言** | 支持中文和英文界面 |

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端（React + Vite）                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │策略编辑 │ │ 回测   │ │组合分析 │ │实盘交易 │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  后端（FastAPI + Backtrader）            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │回测引擎 │ │优化器  │ │任务队列 │ │ WebSocket│       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                      数据层                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│  │ SQLite  │ │Yahoo/EODHD│ │交易所API│                   │
│  └─────────┘ └─────────┘ └─────────┘                   │
└─────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Windows / Linux / macOS

### 安装步骤

#### 1. 克隆仓库

```bash
git clone <repository-url>
cd backtrader
```

#### 2. 后端配置

```bash
cd backend
pip install -r requirements.txt
cp .env.template .env
# 编辑 .env 文件，配置必要的环境变量
```

#### 3. 前端构建

```bash
cd frontend
npm install
npm run build
```

#### 4. 启动服务

**Windows:**
```bash
# 构建并启动
build.bat
start_server.bat
```

**Linux/macOS:**
```bash
cd backend
python main.py
```

#### 5. 访问平台

打开浏览器访问 `http://localhost:8000`

### 首次使用流程

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. 编写策略  │ ─► │  2. 运行回测  │ ─► │  3. 分析结果  │
│  (策略维护)   │    │  (运行策略)   │    │  (查看指标)   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                                       │
        ▼                                       ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  6. 实盘交易  │ ◄─ │  5. 验证优化  │ ◄─ │  4. 组合回测  │
│  (模拟/真实)  │    │  (走向前优化) │    │  (多资产)    │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 功能模块

### 1. 策略开发与维护

**路径**: 侧边栏 → 策略维护

策略维护页面是策略开发的核心工作区，提供专业的代码编辑环境。

#### 功能特点

| 功能 | 说明 |
|------|------|
| **代码编辑器** | Monaco Editor，支持 Python 语法高亮 |
| **AI 分析** | 使用 AI 分析策略代码，获取优化建议 |
| **版本控制** | 自动保存历史版本，支持回滚 |
| **模板库** | 内置策略模板，快速开始 |

#### 操作指南

**新建策略：**
1. 点击 "新建策略" 按钮
2. 输入策略名称（英文，无空格）
3. 选择模板或从空白开始
4. 编写策略代码
5. 点击 "保存" 保存策略

**AI 分析：**
1. 打开已有策略
2. 点击 "AI 分析" 按钮
3. 等待 AI 返回分析结果
4. 根据建议优化策略

**版本管理：**
1. 点击 "版本历史" 查看所有版本
2. 选择版本查看差异对比
3. 点击 "回滚" 恢复到指定版本

#### 策略代码示例

```python
import backtrader as bt

class UserStrategy(bt.Strategy):
    """
    简单均线交叉策略
    """
    params = (
        ('fast_period', 10),   # 快速均线周期
        ('slow_period', 30),   # 慢速均线周期
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(
            self.data.close,
            period=self.params.fast_period
        )
        self.slow_ma = bt.indicators.SMA(
            self.data.close,
            period=self.params.slow_period
        )
        self.crossover = bt.indicators.CrossOver(
            self.fast_ma,
            self.slow_ma
        )

    def next(self):
        if not self.position:
            if self.crossover > 0:  # 金叉买入
                self.buy()
        elif self.crossover < 0:    # 死叉卖出
            self.close()
```

---

### 2. 单资产回测

**路径**: 侧边栏 → 运行策略

单资产回测用于测试策略在单个标的上的表现。

#### 配置参数

| 参数 | 说明 | 示例 |
|------|------|------|
| **策略** | 选择要运行的策略 | sma_cross |
| **标的代码** | 股票/加密货币代码 | AAPL, BTC-USD |
| **开始日期** | 回测起始日期 | 2023-01-01 |
| **结束日期** | 回测结束日期 | 2024-01-01 |
| **初始资金** | 起始资金量 | 100000 |
| **手续费** | 每笔交易费率 | 0.001 (0.1%) |

#### 仓位管理

系统支持多种仓位管理方式：

| 类型 | 说明 | 参数 |
|------|------|------|
| **fixed_size** | 固定手数 | size: 交易数量 |
| **percent** | 资金百分比 | percent: 仓位比例 |
| **risk_percent** | 风险百分比 | risk_percent: 每笔风险比例 |

#### 回测结果

回测完成后，您将看到：

**绩效指标：**
- 总收益率
- 年化收益率
- 最大回撤
- 夏普比率
- 卡玛比率
- 胜率
- 盈亏比

**图表展示：**
- K 线图叠加权益曲线
- 买卖点标记
- 技术指标显示

**交易记录：**
- 每笔交易的开仓/平仓时间
- 交易价格和数量
- 单笔盈亏

#### 深度分析

点击 "深度分析" 可获取更详细的分析：

| 分析类型 | 说明 |
|----------|------|
| **月度收益热力图** | 按月份展示收益分布 |
| **滚动指标** | 滚动夏普、滚动回撤等 |
| **收益分布** | 收益率分布直方图 |
| **回撤分析** | 详细回撤周期分析 |
| **连续亏损统计** | 最大连续亏损次数和金额 |

---

### 3. 投资组合回测

**路径**: 侧边栏 → 组合回测

投资组合回测支持多资产同时回测，分析资产配置效果。

#### 配置步骤

**Step 1: 添加资产**
1. 输入标的代码（如 AAPL）
2. 设置权重（如 30%）
3. 点击 "添加" 按钮
4. 重复添加其他资产

**Step 2: 权重管理**
- 点击 "等权" 自动分配相等权重
- 点击 "标准化" 确保权重总和为 100%
- 手动调整各资产权重

**Step 3: 策略参数**
- 选择策略
- 配置公共参数
- 可选：为每个资产配置独立参数

**Step 4: 运行回测**
- 点击 "运行回测" 开始
- 任务将提交到后台执行

#### 组合分析结果

| 指标类型 | 说明 |
|----------|------|
| **组合指标** | 加权夏普、组合最大回撤、组合收益率 |
| **资产表现** | 各资产独立收益和贡献度 |
| **相关性矩阵** | 资产间相关性热力图 |
| **权益曲线** | 组合整体权益变化 |
| **再平衡时间线** | 再平衡操作记录 |
| **资产贡献图** | 各资产对收益的贡献 |

#### Markowitz 优化

系统提供马科维茨优化建议：
- 最大夏普组合权重
- 最小风险组合权重
- 有效前沿可视化

---

### 4. 走向前优化

**路径**: 侧边栏 → 走向前优化

走向前优化（Walk-Forward Optimization）是验证策略是否过拟合的重要工具。

#### 工作原理

```
时间轴 ─────────────────────────────────────────────────►

窗口1: [====训练期====][==验证期==]
窗口2:      [====训练期====][==验证期==]
窗口3:           [====训练期====][==验证期==]
窗口4:                [====训练期====][==验证期==]
```

- **训练期（In-Sample）**: 优化策略参数
- **验证期（Out-of-Sample）**: 测试参数在未知数据上的表现

#### 配置参数

| 参数 | 说明 | 建议值 |
|------|------|--------|
| **训练期长度** | 样本内数据天数 | 252（1年） |
| **验证期长度** | 样本外数据天数 | 63（1季度） |
| **窗口步进** | 每次滑动天数 | 21（1月） |
| **参数网格** | 待优化的参数范围 | 根据策略设定 |

#### 结果解读

**过拟合评分：**
- ⬇️ **低评分（< 30%）**: 策略稳健，过拟合风险低
- ➡️ **中等评分（30-60%）**: 需要关注，建议增加验证
- ⬆️ **高评分（> 60%）**: 过拟合风险高，需重新设计策略

**参数稳定性：**
- 观察各窗口最优参数的变化
- 参数变化剧烈说明策略不稳定
- 稳定参数更适合实盘使用

**性能对比：**
- 对比训练期和验证期的夏普比率
- 验证期表现远低于训练期说明过拟合

---

### 5. 回测历史

**路径**: 侧边栏 → 回测历史

回测历史页面展示所有历史回测记录。

#### 功能特点

| 功能 | 说明 |
|------|------|
| **分类查看** | 切换单资产回测和组合回测 |
| **筛选过滤** | 按标的、策略、日期筛选 |
| **排序** | 按时间、收益率等排序 |
| **详情查看** | 点击查看完整回测结果 |
| **删除记录** | 清理不需要的历史记录 |

#### 回测对比

选择多个回测记录进行对比：
- 绩效指标对比表
- 权益曲线叠加图
- 风险指标对比

---

### 6. 实盘交易

**路径**: 侧边栏 → 实盘交易

实盘交易模块支持模拟盘和真实交易。

#### 支持的交易所

| 类型 | 交易所 | 说明 |
|------|--------|------|
| **加密货币** | Binance | 需要 CCXT 适配器 |
| **加密货币** | OKX | 需要 CCXT 适配器 |
| **加密货币** | Bybit | 需要 CCXT 适配器 |
| **传统证券** | Interactive Brokers | 需要 IBKR 网关 |

#### 模拟盘使用

**强烈建议先使用模拟盘测试！**

1. 获取测试网 API 密钥
   - Binance 测试网: https://testnet.binance.vision/
2. 在设置中配置 Paper 模式 API
3. 启动模拟交易会话

#### 实盘操作流程

**Step 1: 配置凭证**
1. 进入 设置 → Exchange 凭证
2. 输入交易所 API Key 和 Secret
3. 测试连接

**Step 2: 启动交易**
1. 选择策略和交易对
2. 配置订单大小和风险参数
3. 点击 "开始交易"

**Step 3: 监控仪表板**
- 实时持仓价值
- 未实现盈亏
- 胜率统计
- 订单历史

**Step 4: 停止交易**
- 点击 "停止" 结束交易会话
- 系统会平掉所有持仓（可配置）

#### 风险控制

在 `broker_config.json` 中配置：

```json
{
  "risk_limits": {
    "max_position_size": 10000,    // 最大持仓量
    "max_daily_loss": 1000,        // 日最大亏损
    "max_positions_count": 5       // 最大持仓数
  }
}
```

---

### 7. 报告中心

**路径**: 侧边栏 → 报告中心

报告中心用于生成和管理专业回测报告。

#### 报告类型

| 类型 | 说明 |
|------|------|
| **回测报告** | 单资产回测详细报告 |
| **组合报告** | 投资组合回测报告 |
| **优化报告** | 走向前优化结果报告 |
| **对比报告** | 多策略/多参数对比报告 |

#### 生成报告

1. 在回测结果页面点击 "生成报告"
2. 选择报告类型和包含的内容
3. 等待后台生成完成

#### 报告分享

1. 在报告列表中点击 "分享"
2. 系统生成唯一分享链接
3. 收到链接的人无需登录即可查看
4. 可随时撤销分享权限

---

### 8. 数据管理

**路径**: 侧边栏 → 数据管理

数据管理页面用于管理市场数据缓存。

#### 功能说明

| 功能 | 说明 |
|------|------|
| **缓存统计** | 查看磁盘使用量和数据条数 |
| **数据清理** | 清除指定标的或全部缓存 |
| **数据重采样** | 将分钟数据聚合为小时/日数据 |
| **数据预热** | 提前下载即将使用的数据 |

#### 数据源说明

| 数据源 | 说明 | 适用场景 |
|--------|------|----------|
| **Yahoo Finance** | 免费，延迟数据 | 股票、ETF 回测 |
| **EODHD** | 付费，高质量数据 | 专业分析 |
| **Database** | 本地数据库 | 自有数据 |

---

### 9. 任务中心

**路径**: 侧边栏 → 任务中心

任务中心用于监控后台异步任务。

#### 任务类型

| 类型 | 说明 |
|------|------|
| **backtest** | 单资产回测任务 |
| **portfolio** | 组合回测任务 |
| **walkforward** | 走向前优化任务 |
| **deep_analysis** | 深度分析任务 |

#### 任务状态

| 状态 | 说明 |
|------|------|
| **Pending** | 等待执行 |
| **Running** | 正在执行 |
| **Completed** | 执行完成 |
| **Failed** | 执行失败 |
| **Cancelled** | 已取消 |

#### 操作说明

- **取消**: 取消等待中或运行中的任务
- **重试**: 重新执行失败的任务
- **删除**: 删除任务记录
- **查看结果**: 跳转到任务结果页面

---

### 10. 系统设置

**路径**: 侧边栏 → 设置

#### AI 配置

配置 AI 分析使用的模型：

| 选项 | 说明 |
|------|------|
| **claude-3-sonnet** | Claude 模型 |
| **gpt-4** | OpenAI GPT-4 |
| **gpt-3.5-turbo** | OpenAI GPT-3.5 |

#### OpenAI 凭证

- API Key: 输入 OpenAI API 密钥
- Base URL: 自定义 API 端点（可选）

#### 数据源设置

配置数据获取优先级：
1. Yahoo Finance（默认，免费）
2. EODHD（需要 API Key）
3. Database（本地数据）

#### 交易所凭证

配置各交易所的 API 凭证：
- Binance Paper / Live
- OKX Paper / Live
- Bybit Paper / Live

---

## 策略编写指南

### 策略基本结构

```python
import backtrader as bt

class UserStrategy(bt.Strategy):
    """
    策略类必须命名为 UserStrategy
    """

    # 策略参数定义
    params = (
        ('param1', default_value),
        ('param2', default_value),
    )

    def __init__(self):
        """
        初始化指标
        只在策略开始时调用一次
        """
        pass

    def next(self):
        """
        每根K线调用一次
        在这里编写交易逻辑
        """
        pass

    def notify_order(self, order):
        """
        订单状态变化时调用
        可选实现
        """
        pass

    def notify_trade(self, trade):
        """
        交易完成时调用
        可选实现
        """
        pass
```

### 常用 API

#### 数据访问

```python
# 当前收盘价
self.data.close[0]

# 前一根K线收盘价
self.data.close[-1]

# 开高低收成交量
self.data.open[0]
self.data.high[0]
self.data.low[0]
self.data.close[0]
self.data.volume[0]

# 当前日期时间
self.data.datetime.date(0)
```

#### 下单操作

```python
# 买入
self.buy()
self.buy(size=100)  # 指定数量
self.buy(price=100, exectype=bt.Order.Limit)  # 限价单

# 卖出
self.sell()
self.sell(size=100)

# 平仓
self.close()  # 平掉当前持仓

# 设置止损止盈
self.buy_bracket(
    limitprice=110,   # 止盈价
    stopprice=95,     # 止损价
)
```

#### 持仓信息

```python
# 是否有持仓
if self.position:
    pass

# 持仓数量
self.position.size

# 持仓成本
self.position.price

# 账户价值
self.broker.getvalue()

# 可用现金
self.broker.getcash()
```

### 常用指标

```python
# 简单移动平均
bt.indicators.SMA(self.data.close, period=20)

# 指数移动平均
bt.indicators.EMA(self.data.close, period=20)

# MACD
bt.indicators.MACD(self.data.close)

# RSI
bt.indicators.RSI(self.data.close, period=14)

# 布林带
bt.indicators.BollingerBands(self.data.close, period=20)

# ATR
bt.indicators.ATR(self.data, period=14)

# 均线交叉信号
bt.indicators.CrossOver(fast_ma, slow_ma)
```

### 策略示例：海龟交易法

```python
import backtrader as bt

class UserStrategy(bt.Strategy):
    """
    海龟交易法则简化版
    """
    params = (
        ('entry_period', 20),    # 入场突破周期
        ('exit_period', 10),     # 出场突破周期
        ('atr_period', 14),      # ATR周期
        ('risk_percent', 0.02),  # 单笔风险
    )

    def __init__(self):
        self.high_channel = bt.indicators.Highest(
            self.data.high,
            period=self.params.entry_period
        )
        self.low_channel = bt.indicators.Lowest(
            self.data.low,
            period=self.params.entry_period
        )
        self.exit_high = bt.indicators.Highest(
            self.data.high,
            period=self.params.exit_period
        )
        self.exit_low = bt.indicators.Lowest(
            self.data.low,
            period=self.params.exit_period
        )
        self.atr = bt.indicators.ATR(
            self.data,
            period=self.params.atr_period
        )

        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # 突破最高点买入
            if self.data.close[0] > self.high_channel[-1]:
                risk = self.params.risk_percent * self.broker.getvalue()
                size = int(risk / self.atr[0])
                self.order = self.buy(size=size)
            # 突破最低点卖出
            elif self.data.close[0] < self.low_channel[-1]:
                risk = self.params.risk_percent * self.broker.getvalue()
                size = int(risk / self.atr[0])
                self.order = self.sell(size=size)
        else:
            # 持多头时跌破出场低点平仓
            if self.position.size > 0:
                if self.data.close[0] < self.exit_low[-1]:
                    self.order = self.close()
            # 持空头时突破出场高点平仓
            elif self.position.size < 0:
                if self.data.close[0] > self.exit_high[-1]:
                    self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.order = None
```

---

## 常见问题

### Q1: 回测结果与实盘差异较大怎么办？

**原因：**
- 滑点未考虑
- 手续费设置不准确
- 使用了未来数据（Look-ahead bias）
- 过拟合历史数据

**解决方案：**
1. 增加合理的滑点设置
2. 使用真实的手续费率
3. 确保 `__init__` 中只定义指标，不使用未来数据
4. 使用走向前优化验证策略

### Q2: 策略加载失败怎么办？

**检查项：**
1. 策略类是否命名为 `UserStrategy`
2. 是否有语法错误
3. 依赖包是否安装
4. 参数定义格式是否正确

### Q3: 数据获取失败怎么办？

**排查步骤：**
1. 检查网络连接
2. 验证标的代码是否正确
3. 检查日期范围是否有效
4. 查看数据源 API 是否配置正确

### Q4: 实盘交易不执行订单？

**检查项：**
1. API 凭证是否正确
2. 是否有足够余额
3. 交易对是否支持
4. 订单大小是否满足最小要求
5. 查看后端日志获取详细错误

### Q5: 如何提高回测速度？

**优化建议：**
1. 减少指标计算复杂度
2. 使用较低频率的数据（日线 vs 分钟线）
3. 启用 Worker Pool 并行执行
4. 预热常用数据到缓存

---

## 附录

### A. 环境变量说明

| 变量 | 说明 | 示例 |
|------|------|------|
| `ENABLE_LOGIN` | 启用登录认证 | true/false |
| `OPENAI_API_KEY` | OpenAI API 密钥 | sk-xxx |
| `WORKER_POOL_ENABLED` | 启用工作池 | true/false |
| `WORKER_POOL_SIZE` | 工作池大小 | 4 |
| `DATABASE_URL` | 数据库连接 | sqlite:///trading.db |

### B. API 端点列表

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/backtest` | POST | 执行单资产回测 |
| `/api/portfolio/backtest` | POST | 执行组合回测 |
| `/api/walkforward` | POST | 执行走向前优化 |
| `/api/strategy` | GET/POST | 策略管理 |
| `/api/tasks` | GET | 获取任务列表 |
| `/api/reports` | GET/POST | 报告管理 |
| `/api/settings` | GET/PUT | 系统设置 |
| `/api/live/start` | POST | 启动实盘交易 |
| `/api/live/stop` | POST | 停止实盘交易 |

### C. 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + S` | 保存策略 |
| `Ctrl + Enter` | 运行回测 |
| `Escape` | 关闭弹窗 |

### D. 版本更新日志

请查看项目根目录的 `CHANGELOG.md` 文件。

---

## 技术支持

如遇问题，请通过以下方式获取帮助：

1. 查阅本文档和项目 README
2. 检查 `docs/` 目录下的其他文档
3. 在 GitHub Issues 中搜索或提交问题

---

## 高级功能

### 11. 深度分析详解

深度分析模块提供全面的回测性能分析工具，帮助用户深入理解策略行为。

#### 11.1 月度收益热力图

以年月矩阵形式展示收益分布：

```
        1月    2月    3月    4月    5月    ...
2022   +2.3%  -1.5%  +4.2%  +0.8%  -0.5%  ...
2023   +1.8%  +3.1%  -2.0%  +1.5%  +2.8%  ...
2024   +0.5%  +2.2%  +1.8%  ...
```

**应用场景：**
- 识别季节性模式（如"五穷六绝"）
- 发现策略在特定月份的表现规律
- 评估策略的时间稳定性

#### 11.2 滚动夏普比率

计算滑动窗口内的夏普比率变化：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| **窗口大小** | 60天 | 计算周期 |
| **基准** | SPY / 沪深300 | 对比标的 |
| **无风险利率** | 2% | 年化无风险收益 |

**解读要点：**
- 夏普持续 > 1.0 表示策略稳定盈利
- 夏普波动剧烈说明策略不稳定
- 与基准对比可评估相对表现

#### 11.3 收益分布分析

提供详细的统计指标：

| 指标 | 说明 | 理想值 |
|------|------|--------|
| **均值（Mean）** | 日均收益 | > 0 |
| **标准差（Std）** | 收益波动 | 越小越好 |
| **偏度（Skewness）** | 分布不对称性 | > 0（右偏） |
| **峰度（Kurtosis）** | 尾部厚度 | 接近 3（正态） |
| **VaR 95%** | 在险价值 | 可接受范围内 |
| **CVaR 95%** | 条件在险价值 | 可接受范围内 |

**VaR 解释：**
- VaR 95% = -2.5% 表示：有 5% 的概率日亏损超过 2.5%
- CVaR 是超过 VaR 时的平均亏损

#### 11.4 回撤分析

详细展示回撤周期：

```
┌─────────────────────────────────────────────────────┐
│ 回撤分布直方图                                        │
│                                                      │
│  ████████████████████  30次 (0-5%)                   │
│  ██████████████        20次 (5-10%)                  │
│  ████████              10次 (10-15%)                 │
│  ███                    5次 (15-20%)                 │
│  █                      2次 (> 20%)                  │
└─────────────────────────────────────────────────────┘

主要回撤期间：
┌─────────────┬─────────────┬──────────┬──────────┐
│ 开始日期     │ 结束日期     │ 深度     │ 持续天数  │
├─────────────┼─────────────┼──────────┼──────────┤
│ 2022-06-01  │ 2022-06-15  │ -15.2%   │ 14天     │
│ 2023-03-10  │ 2023-03-25  │ -12.8%   │ 15天     │
│ 2023-09-05  │ 2023-09-12  │ -8.5%    │ 7天      │
└─────────────┴─────────────┴──────────┴──────────┘
```

#### 11.5 连续亏损统计

检测策略的最大连亏情况：

| 指标 | 说明 |
|------|------|
| **最大连亏天数** | 连续亏损的最长天数 |
| **最大连亏周期** | 起止日期 |
| **最大连亏金额** | 该周期内的累计亏损 |
| **连亏分布** | 各连亏长度的频次 |

**重要性：**
- 评估策略的心理承受要求
- 设计合理的止损策略
- 资金管理参考

#### 11.6 基准对比

与市场基准进行全面对比：

| 指标 | 计算方式 | 解释 |
|------|----------|------|
| **相关性** | Pearson 相关系数 | 与市场的关联程度 |
| **Beta** | Cov(R, Rm) / Var(Rm) | 系统性风险敞口 |
| **Alpha** | R - Rf - Beta * (Rm - Rf) | 超额收益能力 |
| **信息比率** | (R - Rm) / TE | 主动管理能力 |
| **跟踪误差** | Std(R - Rm) | 与基准的偏离程度 |

**基准选择：**
- **美股策略**: SPY（标普500 ETF）
- **A 股策略**: 000300.SS（沪深300）
- **加密货币**: BTC-USD

---

### 12. PyFolio 导出与分析

系统支持将回测结果导出为 PyFolio 兼容格式，或生成 QuantStats 专业分析报告。

#### 12.1 导出 PyFolio 格式

**导出内容：**

```
pyfolio_export.zip
├── returns.csv          # 日收益率序列
├── transactions.csv     # 交易记录
├── positions.csv        # 持仓价值
├── metadata.json        # 导出元数据
└── README.md            # 使用说明
```

**使用方法：**

```python
import pyfolio as pf
import pandas as pd

# 加载导出数据
returns = pd.read_csv('returns.csv', index_col=0, parse_dates=True)['returns']
transactions = pd.read_csv('transactions.csv', index_col=0, parse_dates=True)

# 生成完整分析
pf.create_full_tear_sheet(returns, transactions=transactions)
```

#### 12.2 生成 QuantStats 报告

一键生成 HTML 格式的专业分析报告：

**报告内容：**
- 累计收益曲线
- 月度收益表格
- 回撤分析图
- 滚动波动率
- 详细绩效指标
- 与基准对比

**API 调用：**

```bash
POST /api/backtest/{backtest_id}/tear-sheet
```

#### 12.3 绩效指标导出

可单独获取计算的绩效指标：

| 指标 | 说明 |
|------|------|
| **年化收益率** | 年化后的总收益 |
| **年化波动率** | 收益的年化标准差 |
| **夏普比率** | 风险调整后收益 |
| **索提诺比率** | 仅考虑下行风险 |
| **卡玛比率** | 收益 / 最大回撤 |
| **胜率** | 盈利交易占比 |
| **交易天数** | 有效交易天数 |

---

### 13. 投资组合优化算法

系统内置四种组合优化算法，可在再平衡时自动调整权重。

#### 13.1 等权配置（Equal Weight）

**原理：**
- 每个资产分配相等权重
- N 个资产，每个权重 = 1/N

**优点：**
- 简单易懂，无需历史数据
- 避免集中度风险
- 作为基准对比

**缺点：**
- 未考虑风险差异
- 可能过度配置高波动资产

#### 13.2 风险平价（Risk Parity）

**原理：**
- 每个资产贡献相等的风险
- 波动率高的资产权重低

**数学表达：**
```
目标: 使每个资产的风险贡献相等
RC_i = w_i * (Σw)_i / σ_p = 1/N * σ_p

其中：
- w_i: 资产 i 的权重
- (Σw)_i: 协方差矩阵乘权重向量的第 i 个元素
- σ_p: 组合波动率
```

**优点：**
- 分散风险来源
- 不依赖收益预测
- 在不同市场环境下表现稳定

**适用场景：**
- 长期资产配置
- 风险控制优先

#### 13.3 最小方差（Minimum Variance）

**原理：**
- 最小化组合波动率
- 不考虑预期收益

**数学表达：**
```
min   w' Σ w
s.t.  Σ w_i = 1
      w_i >= 0
```

**优点：**
- 降低整体波动
- 仅需协方差矩阵（相对稳定）

**缺点：**
- 可能过度集中于低波动资产
- 忽略收益差异

#### 13.4 马科维茨优化（Markowitz / Max Sharpe）

**原理：**
- 在给定风险下最大化收益
- 或最大化夏普比率

**数学表达：**
```
max   (w' μ - r_f) / sqrt(w' Σ w)
s.t.  Σ w_i = 1
      w_i >= 0

其中：
- μ: 预期收益向量
- r_f: 无风险利率
- Σ: 协方差矩阵
```

**优点：**
- 理论完备，最优风险收益权衡

**缺点：**
- 对输入参数敏感（收益预测难）
- 可能产生极端权重

**建议：**
- 结合约束条件（最大权重限制）
- 使用稳健估计（Ledoit-Wolf 收缩）

#### 13.5 优化方法对比

| 方法 | 需要收益预测 | 稳健性 | 计算复杂度 |
|------|-------------|--------|-----------|
| 等权 | 否 | 高 | O(1) |
| 风险平价 | 否 | 高 | O(n²) |
| 最小方差 | 否 | 中 | O(n²) |
| 马科维茨 | 是 | 低 | O(n²) |

---

### 14. 再平衡策略配置

#### 14.1 再平衡频率

| 频率 | 说明 | 适用场景 |
|------|------|----------|
| **monthly** | 每月第一个交易日 | 常规配置 |
| **monthly_first** | 每月第一个交易日 | 同上 |
| **monthly_last** | 每月最后一个交易日 | 避免月初波动 |
| **quarterly** | 每季度第一个交易日 | 减少交易成本 |
| **quarterly_first** | 季度第一天 | 同上 |
| **quarterly_last** | 季度最后一天 | 避免季度效应 |
| **annually** | 每年第一个交易日 | 长期投资 |
| **annually_first** | 年度第一天 | 同上 |
| **annually_last** | 年度最后一天 | 年终配置 |

#### 14.2 交易阈值

```json
{
  "rebalance_config": {
    "frequency": "monthly",
    "min_trade_threshold": 0.01,    // 权重偏离 < 1% 不交易
    "transaction_cost_pct": 0.001   // 0.1% 交易成本
  }
}
```

**阈值作用：**
- 避免微小调整产生的交易成本
- 减少实际交易次数
- 提高净收益

#### 14.3 交易成本建模

系统在回测中考虑真实交易成本：

| 成本类型 | 说明 |
|----------|------|
| **佣金** | 每笔交易的固定/比例费用 |
| **滑点** | 预期成交价与实际价差 |
| **冲击成本** | 大单对市场的影响 |

---

### 15. 单资产参数定制

在组合回测中，可为每个资产配置独立的策略参数。

#### 15.1 支持的参数类型

| 参数组 | 参数名 | 说明 | 范围 |
|--------|--------|------|------|
| **趋势** | sma_period | 简单均线周期 | 5-200 |
| | ema_period | 指数均线周期 | 5-200 |
| **动量** | rsi_period | RSI 周期 | 2-50 |
| | rsi_oversold | RSI 超卖阈值 | 10-40 |
| | rsi_overbought | RSI 超买阈值 | 60-90 |
| **MACD** | macd_fast | 快线周期 | 5-20 |
| | macd_slow | 慢线周期 | 15-50 |
| | macd_signal | 信号线周期 | 5-20 |
| **波动** | bb_period | 布林带周期 | 10-50 |
| | bb_std | 布林带标准差 | 1.0-3.0 |
| | atr_period | ATR 周期 | 5-30 |

#### 15.2 配置示例

```json
{
  "per_asset_params": {
    "AAPL": {
      "sma_period": 20,
      "rsi_period": 14,
      "rsi_oversold": 30
    },
    "GOOGL": {
      "ema_period": 12,
      "macd_fast": 12,
      "macd_slow": 26
    },
    "MSFT": {
      "bb_period": 20,
      "bb_std": 2.0,
      "atr_period": 14
    }
  }
}
```

#### 15.3 前端配置界面

1. 开启 "单资产参数" 开关
2. 展开各资产的参数面板
3. 修改需要定制的参数
4. 使用 "应用到全部" 批量设置
5. 使用 "重置" 恢复默认值

---

## 更多策略示例

### 策略示例：布林带均值回归

```python
import backtrader as bt

class UserStrategy(bt.Strategy):
    """
    布林带均值回归策略
    价格触及下轨买入，触及上轨卖出
    """
    params = (
        ('period', 20),      # 布林带周期
        ('devfactor', 2.0),  # 标准差倍数
        ('size', 100),       # 交易数量
    )

    def __init__(self):
        self.boll = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.period,
            devfactor=self.params.devfactor
        )
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # 价格触及下轨，买入
            if self.data.close[0] < self.boll.lines.bot[0]:
                self.order = self.buy(size=self.params.size)
        else:
            # 价格触及上轨或中轨，卖出
            if self.data.close[0] > self.boll.lines.top[0]:
                self.order = self.close()
            elif self.data.close[0] > self.boll.lines.mid[0]:
                # 可选：触及中轨部分平仓
                pass

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Rejected]:
            self.order = None
```

### 策略示例：RSI 超买超卖

```python
import backtrader as bt

class UserStrategy(bt.Strategy):
    """
    RSI 超买超卖策略
    """
    params = (
        ('rsi_period', 14),
        ('oversold', 30),
        ('overbought', 70),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(
            self.data.close,
            period=self.params.rsi_period
        )
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # RSI 超卖区买入
            if self.rsi[0] < self.params.oversold:
                self.order = self.buy()
        else:
            # RSI 超买区卖出
            if self.rsi[0] > self.params.overbought:
                self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.order = None
```

### 策略示例：MACD 动量策略

```python
import backtrader as bt

class UserStrategy(bt.Strategy):
    """
    MACD 动量交叉策略
    """
    params = (
        ('fast', 12),
        ('slow', 26),
        ('signal', 9),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.fast,
            period_me2=self.params.slow,
            period_signal=self.params.signal
        )
        # MACD 线与信号线的交叉
        self.crossover = bt.indicators.CrossOver(
            self.macd.macd,
            self.macd.signal
        )
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # MACD 金叉且 MACD > 0
            if self.crossover > 0 and self.macd.macd[0] > 0:
                self.order = self.buy()
        else:
            # MACD 死叉
            if self.crossover < 0:
                self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.order = None
```

### 策略示例：多时间框架策略

```python
import backtrader as bt

class UserStrategy(bt.Strategy):
    """
    多时间框架策略
    使用日线判断趋势，小时线寻找入场点
    """
    params = (
        ('trend_period', 50),   # 趋势判断周期
        ('entry_period', 20),   # 入场信号周期
    )

    def __init__(self):
        # 假设 data0 是小时线，data1 是日线
        # 日线趋势判断
        self.trend_ma = bt.indicators.SMA(
            self.data1.close,
            period=self.params.trend_period
        )
        # 小时线入场信号
        self.entry_ma = bt.indicators.SMA(
            self.data0.close,
            period=self.params.entry_period
        )
        self.order = None

    def next(self):
        if self.order:
            return

        # 确保日线数据可用
        if len(self.data1) < self.params.trend_period:
            return

        # 判断趋势方向（日线）
        trend_up = self.data1.close[0] > self.trend_ma[0]
        trend_down = self.data1.close[0] < self.trend_ma[0]

        if not self.position:
            # 上升趋势中，价格回调到均线附近买入
            if trend_up:
                if self.data0.close[0] > self.entry_ma[0]:
                    if self.data0.close[-1] <= self.entry_ma[-1]:
                        self.order = self.buy()
        else:
            # 趋势反转时平仓
            if trend_down:
                self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.order = None
```

### 策略示例：网格交易策略

```python
import backtrader as bt

class UserStrategy(bt.Strategy):
    """
    简单网格交易策略
    在价格区间内分批建仓
    """
    params = (
        ('grid_num', 5),          # 网格数量
        ('grid_range', 0.10),     # 网格总范围（10%）
        ('base_price', None),     # 基准价格（None则使用首日收盘价）
        ('position_per_grid', 100),  # 每格仓位
    )

    def __init__(self):
        self.base_price = None
        self.grid_prices = []
        self.grid_positions = {}  # 记录每个网格的持仓

    def start(self):
        # 初始化网格
        if self.params.base_price:
            self.base_price = self.params.base_price
        else:
            self.base_price = self.data.close[0]

        half_range = self.params.grid_range / 2
        step = self.params.grid_range / self.params.grid_num

        for i in range(self.params.grid_num + 1):
            price = self.base_price * (1 - half_range + i * step)
            self.grid_prices.append(price)
            self.grid_positions[i] = 0

    def next(self):
        current_price = self.data.close[0]

        for i, grid_price in enumerate(self.grid_prices[:-1]):
            next_grid = self.grid_prices[i + 1]

            # 价格跌破网格线且该网格无仓位，买入
            if current_price < grid_price and self.grid_positions[i] == 0:
                self.buy(size=self.params.position_per_grid)
                self.grid_positions[i] = 1

            # 价格突破上一网格线且该网格有仓位，卖出
            if current_price > next_grid and self.grid_positions[i] == 1:
                self.sell(size=self.params.position_per_grid)
                self.grid_positions[i] = 0
```

---

## 最佳实践

### 策略开发最佳实践

#### 1. 避免过拟合

| 做法 | 说明 |
|------|------|
| **简化参数** | 参数越少，过拟合风险越低 |
| **走向前验证** | 使用样本外数据验证 |
| **多市场测试** | 在不同市场验证策略普适性 |
| **逻辑优先** | 基于市场逻辑而非数据挖掘 |

#### 2. 代码质量

```python
# 推荐做法
class UserStrategy(bt.Strategy):
    params = (
        ('period', 20),  # 明确注释每个参数
    )

    def __init__(self):
        # 所有指标在这里初始化
        self.sma = bt.indicators.SMA(
            self.data.close,
            period=self.params.period
        )

    def next(self):
        # 简洁的交易逻辑
        if not self.position and self.data.close[0] > self.sma[0]:
            self.buy()
```

#### 3. 风险管理

```python
def next(self):
    # 始终检查资金情况
    available_cash = self.broker.getcash()
    position_value = self.broker.getvalue() - available_cash

    # 控制单笔风险
    max_risk = 0.02 * self.broker.getvalue()  # 2% 风险

    # 控制总仓位
    max_position = 0.5 * self.broker.getvalue()  # 50% 最大仓位

    if position_value < max_position:
        # 可以开新仓
        pass
```

### 回测最佳实践

#### 1. 合理的回测周期

| 策略类型 | 建议回测周期 | 说明 |
|----------|-------------|------|
| 日内策略 | 1-2 年 | 避免数据量过大 |
| 日线策略 | 5-10 年 | 覆盖不同市场周期 |
| 长期策略 | 10-20 年 | 包含多次牛熊周期 |

#### 2. 真实成本设置

```python
# 股票
commission = 0.001  # 0.1% 佣金（双边）
slippage = 0.001    # 0.1% 滑点

# 期货
commission = 0.0001  # 0.01% 佣金
slippage = 1         # 1 跳滑点

# 加密货币
commission = 0.001   # 0.1% 佣金（Maker）
commission = 0.002   # 0.2% 佣金（Taker）
```

#### 3. 避免常见陷阱

| 陷阱 | 说明 | 解决方案 |
|------|------|----------|
| **前视偏差** | 使用未来数据 | 只在 `next()` 中交易 |
| **幸存者偏差** | 只测试现存股票 | 使用历史成分股 |
| **流动性假设** | 假设无限流动性 | 考虑成交量限制 |
| **数据质量** | 错误的价格数据 | 使用可靠数据源 |

### 实盘交易最佳实践

#### 1. 渐进式上线

```
第1周: 模拟盘测试
  ↓
第2周: 最小仓位实盘（1%资金）
  ↓
第3-4周: 逐步增加仓位（5%→10%→25%）
  ↓
第5周+: 正常仓位运行
```

#### 2. 监控指标

| 指标 | 预警阈值 | 处理方式 |
|------|----------|----------|
| **日亏损** | > 2% | 暂停交易 |
| **周亏损** | > 5% | 降低仓位 |
| **回撤** | > 15% | 全面审查 |
| **连亏天数** | > 5 天 | 检查市场环境 |

#### 3. API 安全

```
✓ 启用 IP 白名单
✓ 禁用提现权限
✓ 使用只读密钥监控
✓ 定期轮换 API 密钥
✓ 加密存储凭证
```

---

## 性能优化

### 回测性能优化

#### 1. 数据预热

```bash
# 提前下载常用数据
POST /api/market-data/cache/warmup
{
  "tickers": ["AAPL", "GOOGL", "MSFT", "AMZN", "META"],
  "start_date": "2020-01-01",
  "end_date": "2024-01-01"
}
```

#### 2. 启用 Worker Pool

```bash
# .env 配置
WORKER_POOL_ENABLED=true
WORKER_POOL_SIZE=4       # CPU 核心数
WORKER_TIMEOUT=300       # 5分钟超时
```

#### 3. 优化指标计算

```python
# 避免在 next() 中重复计算
class UserStrategy(bt.Strategy):
    def __init__(self):
        # 好：在初始化时计算
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        # 好：直接使用预计算的值
        if self.crossover > 0:
            self.buy()

        # 差：每次都计算
        # if self.fast_ma[0] > self.slow_ma[0] and self.fast_ma[-1] <= self.slow_ma[-1]:
        #     self.buy()
```

### 系统性能优化

#### 1. 数据库优化

```sql
-- 定期清理旧数据
DELETE FROM backtest_history WHERE created_at < date('now', '-90 days');

-- 优化数据库
VACUUM;
ANALYZE;
```

#### 2. 缓存管理

```bash
# 清理过期缓存
POST /api/market-data/cache/cleanup
{
  "retention_days": 30
}
```

#### 3. 资源监控

| 资源 | 建议阈值 | 监控命令 |
|------|----------|----------|
| **CPU** | < 80% | `top` / 任务管理器 |
| **内存** | < 80% | `free -h` / 任务管理器 |
| **磁盘** | < 80% | `df -h` / 磁盘管理 |

---

## 部署指南

### Docker 部署

#### 1. 构建镜像

```bash
# 使用优化脚本
bash docker-build-optimized.sh

# 或手动构建
docker build -t backtrader-platform .
```

#### 2. 运行容器

```bash
docker-compose up -d
```

#### 3. 生产环境配置

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    image: backtrader-platform:latest
    environment:
      - ENABLE_LOGIN=true
      - DATABASE_URL=postgresql://user:pass@db:5432/trading
      - WORKER_POOL_ENABLED=true
      - WORKER_POOL_SIZE=4
    volumes:
      - ./data:/app/backend/resources
    ports:
      - "8000:8000"
    restart: always

  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=trading

volumes:
  postgres_data:
```

### 安全配置

#### 1. 环境变量安全

```bash
# 不要在代码中硬编码敏感信息
# 使用环境变量或密钥管理服务

# .env 文件权限
chmod 600 .env
```

#### 2. HTTPS 配置

```nginx
# nginx 反向代理配置
server {
    listen 443 ssl;
    server_name trading.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

#### 3. 认证配置

```bash
# 启用登录认证
ENABLE_LOGIN=true
LOGTO_ISSUER=https://your-logto-instance.com
LOGTO_JWKS_URI=https://your-logto-instance.com/.well-known/jwks.json
```

### 备份策略

```bash
# 数据库备份
sqlite3 trading_sessions.db ".backup backup.db"

# 策略文件备份
tar -czf strategies_backup.tar.gz backend/resources/strategy/

# 配置备份
cp .env .env.backup
cp backend/resources/config/broker_config.json broker_config.backup.json
```

---

## 更多常见问题

### Q6: 如何处理股票分红和拆股？

**解决方案：**
- 使用调整后价格（Adjusted Close）
- Yahoo Finance 默认提供调整后数据
- 回测时选择 "使用调整后价格" 选项

### Q7: 如何回测多个市场？

**方法：**
1. 单独回测各市场
2. 使用组合回测功能
3. 注意时区差异和交易时间

### Q8: 如何导入自定义数据？

**步骤：**
1. 准备 CSV 格式数据
2. 确保包含：Date, Open, High, Low, Close, Volume
3. 上传至 `backend/resources/data/` 目录
4. 配置数据源为 "Database"

### Q9: 回测与实盘时间不同步？

**检查项：**
1. 确保时区设置正确
2. 检查数据源时间戳格式
3. 对齐交易时间段

### Q10: 如何处理高频策略？

**注意事项：**
1. 使用分钟级数据
2. 考虑延迟和滑点影响
3. 设置合理的交易成本
4. 监控 API 调用频率限制

---

## 术语表

| 术语 | 英文 | 解释 |
|------|------|------|
| **回测** | Backtest | 使用历史数据验证策略 |
| **夏普比率** | Sharpe Ratio | 风险调整后收益指标 |
| **最大回撤** | Maximum Drawdown | 从峰值到谷值的最大下跌 |
| **走向前优化** | Walk-Forward | 滚动窗口的参数优化方法 |
| **过拟合** | Overfitting | 过度拟合历史数据 |
| **权益曲线** | Equity Curve | 账户价值随时间变化 |
| **滑点** | Slippage | 预期价格与实际成交价差 |
| **在险价值** | VaR | Value at Risk，潜在损失 |
| **条件在险价值** | CVaR | 超过 VaR 时的平均损失 |
| **Alpha** | Alpha | 相对基准的超额收益 |
| **Beta** | Beta | 系统性风险敞口 |
| **再平衡** | Rebalancing | 调整资产配置至目标权重 |
| **风险平价** | Risk Parity | 等风险贡献配置方法 |

---

## 技术支持

如遇问题，请通过以下方式获取帮助：

1. 查阅本文档和项目 README
2. 检查 `docs/` 目录下的其他文档
3. 在 GitHub Issues 中搜索或提交问题

---

*本文档最后更新时间：2025年12月28日*
