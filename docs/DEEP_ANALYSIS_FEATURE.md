# 深度分析功能实现文档

## 功能概述

回测结果深度分析功能为用户提供高级的策略性能分析工具，包括：

1. **月度收益热图** - 可视化每月收益表现，快速识别季节性模式
2. **滚动 Sharpe 比率** - 展示策略风险调整后收益的时间变化趋势
3. **收益分布分析** - 包含统计指标（均值、标准差、偏度、峰度、VaR、CVaR）
4. **回撤分析** - 展示回撤深度分布和主要回撤期间
5. **连续亏损统计** - 识别最大连亏周期，评估策略稳定性
6. **基准对比** - 与 SPY（美股）和沪深300（A股）对比，计算 Alpha、Beta、相关性等指标

## 实现架构

### 后端实现

#### 新增文件

1. **`backend/src/service/deep_analysis.py`** - 核心分析计算模块
   - `compute_deep_analysis()` - 主入口函数
   - `compute_monthly_returns()` - 月度收益矩阵计算
   - `compute_rolling_sharpe()` - 滚动 Sharpe 计算
   - `compute_returns_distribution()` - 收益分布统计
   - `compute_drawdown_distribution()` - 回撤分布分析
   - `compute_consecutive_losses()` - 连续亏损检测
   - `fetch_benchmark_data()` - 基准数据获取（通过 yfinance）
   - `compute_benchmark_comparison()` - 基准对比指标计算

2. **`backend/src/db/migrate_add_deep_analysis.py`** - 数据库迁移脚本
   - 为现有数据库添加 `deep_analysis` 列
   - 可重复运行，会检查列是否已存在

#### 修改文件

1. **`backend/src/service/backtest_engine.py`**
   - 添加 `TimeReturn` analyzer 收集每日收益率
   - 在 metrics 中添加 `equity_curve` 字段

2. **`backend/src/db/models/backtest.py`**
   - `BacktestHistoryModel` 添加 `deep_analysis` 列（SafeJSON 类型）

3. **`backend/src/db/storage/backtest.py`**
   - 添加 `update_deep_analysis()` 方法 - 保存分析结果
   - 添加 `get_deep_analysis()` 方法 - 获取缓存的分析结果
   - 修改 `_record_to_dict()` 包含 deep_analysis 字段

4. **`backend/src/routes/backtest_routes.py`**
   - 新增 `POST /api/backtest/history/{id}/deep-analysis` 端点
   - 支持配置参数：benchmarks、rolling_window、risk_free_rate
   - 实现缓存机制：首次计算后存储，后续直接返回

### 前端实现

#### 新增组件

所有组件位于 `frontend/src/components/DeepAnalysis/`：

1. **`index.jsx`** - 主容器组件
   - 管理加载状态和数据获取
   - 布局管理（响应式网格）

2. **`MonthlyReturnsHeatmap.jsx`** - 月度收益热图
   - 使用 ECharts heatmap
   - 颜色映射：绿色（正收益）→ 红色（负收益）

3. **`RollingSharpeChart.jsx`** - 滚动 Sharpe 图表
   - 使用 lightweight-charts
   - 支持多条线（策略 + 基准）

4. **`ReturnsDistribution.jsx`** - 收益分布图
   - 使用 ECharts 柱状图
   - 展示统计指标卡片

5. **`DrawdownDistribution.jsx`** - 回撤分析
   - 回撤深度分布直方图
   - 主要回撤期间表格

6. **`ConsecutiveLossStats.jsx`** - 连续亏损统计
   - 最大连亏展示
   - 连亏分布图

7. **`BenchmarkComparison.jsx`** - 基准对比
   - 累计收益曲线图
   - 对比指标表格（Alpha、Beta、相关性、信息比率、跟踪误差）

#### 翻译文件

- `frontend/src/locales/en/deep_analysis.json` - 英文翻译
- `frontend/src/locales/zh/deep_analysis.json` - 中文翻译

#### 修改文件

1. **`frontend/src/services/backtestApi.js`**
   - 添加 `getDeepAnalysis(backtestId, config)` 方法

2. **`frontend/src/components/BacktestHistory/BacktestDetailModal.jsx`**
   - 添加"深度分析"Tab

3. **`frontend/src/pages/RunStrategy.jsx`**
   - 在回测结果下方自动展示深度分析

4. **`frontend/src/i18n.js`**
   - 注册 deep_analysis 命名空间

5. **翻译文件**
   - `frontend/src/locales/en/history.json` - 添加 tab_deep_analysis
   - `frontend/src/locales/zh/history.json` - 添加 tab_deep_analysis

### 文档更新

- `backend/src/routes/routes.md` - 添加新 API 端点说明
- `backend/src/service/service.md` - 添加 deep_analysis.py 模块说明

## 数据流程

```
┌─────────────────┐
│  运行回测       │
│  (backtest)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ TimeReturn Analyzer         │
│ 收集每日收益率 (equity_curve)│
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ 存储到 metrics JSON          │
│ BacktestHistoryModel        │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ 前端请求深度分析             │
│ GET /api/.../deep-analysis  │
└────────┬────────────────────┘
         │
    ┌────┴────┐
    │ 检查缓存 │
    └────┬────┘
         │
    ┌────┴────────┐
    │ 已有缓存？   │
    └─┬─────────┬─┘
      │ 是      │ 否
      │         │
      ▼         ▼
  ┌────────┐  ┌──────────────────────┐
  │ 返回   │  │ 1. 获取 equity_curve │
  │ 缓存   │  │ 2. 获取基准数据       │
  └────────┘  │ 3. 计算各项指标       │
              │ 4. 缓存到数据库       │
              │ 5. 返回结果           │
              └────────┬─────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ 前端渲染图表     │
              │ (6个子组件)      │
              └──────────────────┘
```

## API 详细说明

### 请求端点

```
POST /api/backtest/history/{backtest_id}/deep-analysis
```

### 请求参数（可选）

```json
{
  "benchmarks": ["SPY", "000300.SS"],
  "rolling_window": 60,
  "risk_free_rate": 0.02
}
```

### 响应格式

```json
{
  "status": "ok",
  "computed_at": "2024-01-15T10:30:00Z",
  "config": {
    "benchmarks": ["SPY", "000300.SS"],
    "rolling_window": 60,
    "risk_free_rate": 0.02
  },
  "monthly_returns": {
    "years": [2022, 2023],
    "months": ["Jan", "Feb", ..., "Dec"],
    "matrix": [[0.05, -0.02, ...], ...]
  },
  "rolling_sharpe": {
    "window": 60,
    "strategy": [{"date": "2022-03-01", "value": 1.5}, ...],
    "SPY": [{"date": "2022-03-01", "value": 1.2}, ...],
    "000300.SS": [...]
  },
  "returns_distribution": {
    "bins": [...],
    "strategy_counts": [...],
    "benchmark_counts": {...},
    "statistics": {
      "mean": 0.001,
      "std": 0.015,
      "skewness": -0.2,
      "kurtosis": 3.5,
      "var_95": -0.025,
      "cvar_95": -0.035
    }
  },
  "drawdown_distribution": {
    "bins": [...],
    "counts": [...],
    "max_drawdown": -0.15,
    "avg_drawdown": -0.05,
    "drawdown_periods": [
      {
        "start": "2022-03-01",
        "end": "2022-03-15",
        "depth": -0.08,
        "duration": 14
      },
      ...
    ]
  },
  "consecutive_losses": {
    "max_streak": 5,
    "max_streak_period": {
      "start": "2022-06-01",
      "end": "2022-06-07"
    },
    "max_streak_loss": -0.08,
    "streaks_distribution": {
      "1": 45,
      "2": 20,
      ...
    }
  },
  "benchmark_comparison": {
    "cumulative_returns": {
      "strategy": [...],
      "SPY": [...],
      "000300.SS": [...]
    },
    "correlation": {
      "SPY": 0.65,
      "000300.SS": 0.45
    },
    "beta": {...},
    "alpha": {...},
    "information_ratio": {...},
    "tracking_error": {...}
  }
}
```

## 数据库迁移

### 现有用户升级步骤

1. 运行迁移脚本：
```bash
cd backend
python -m src.db.migrate_add_deep_analysis
```

2. 迁移脚本会自动：
   - 检查 `deep_analysis` 列是否存在
   - 如不存在，添加该列（TEXT 类型，可为 NULL）
   - 不影响现有数据

### 新回测的处理

- 新运行的回测会自动包含 `equity_curve` 数据
- 首次访问深度分析时会计算并缓存结果
- 后续访问直接返回缓存数据

### 历史回测的处理

- 旧回测缺少 `equity_curve` 数据
- 访问深度分析时会提示："请重新运行回测以生成深度分析数据"
- 用户需要重新运行回测以使用此功能

## 使用指南

### 用户视角

#### 1. 在 RunStrategy 页面查看

1. 配置回测参数
2. 点击"Run Backtest"
3. 等待回测完成
4. 页面底部自动展示深度分析（6个图表区域）

#### 2. 在回测历史中查看

1. 访问"回测历史"页面
2. 点击任意回测记录查看详情
3. 切换到"深度分析"Tab
4. 首次访问会计算并缓存
5. 后续访问直接展示

### 开发者视角

#### 添加新的分析指标

1. 在 `backend/src/service/deep_analysis.py` 中添加计算函数
2. 在 `compute_deep_analysis()` 中调用
3. 在前端创建对应的可视化组件
4. 在 `DeepAnalysis/index.jsx` 中集成
5. 添加相应的翻译文本

#### 自定义基准

修改 `DEFAULT_BENCHMARKS` 常量：
```python
# backend/src/service/deep_analysis.py
DEFAULT_BENCHMARKS = ["SPY", "000300.SS", "^GSPC"]
```

#### 调整窗口大小

修改默认值：
```python
# backend/src/service/deep_analysis.py
DEFAULT_ROLLING_WINDOW = 60  # 改为其他天数
```

## 性能考虑

### 计算复杂度

- **月度收益**: O(n) - n 为交易日数量
- **滚动 Sharpe**: O(n * w) - w 为窗口大小
- **收益分布**: O(n * b) - b 为分箱数量
- **回撤分析**: O(n)
- **连续亏损**: O(n)
- **基准对比**: O(n) + 网络请求时间

### 缓存机制

- 计算结果存储在 `BacktestHistoryModel.deep_analysis` 列
- 使用 SafeJSON 类型自动序列化
- 首次计算后立即缓存
- 减少重复计算，提升响应速度

### 基准数据获取

- 通过 `yfinance` 获取
- 利用 `market_data` 表缓存
- 减少外部 API 调用

## 故障排查

### 常见问题

1. **"Equity curve data not available"**
   - 原因：回测是在添加 TimeReturn analyzer 之前运行的
   - 解决：重新运行回测

2. **基准数据获取失败**
   - 原因：网络问题或 ticker 不可用
   - 结果：该基准对比图表不显示，其他图表正常

3. **数据库迁移失败**
   - 检查数据库连接
   - 确认有写权限
   - 查看错误日志

4. **图表不显示**
   - 检查浏览器控制台错误
   - 确认数据格式正确
   - 验证翻译文件加载

### 日志调试

```python
# 在 deep_analysis.py 中查看日志
import logging
logger = logging.getLogger(__name__)
```

前端调试：
```javascript
// 在浏览器控制台查看
console.log('Analysis data:', analysisData)
```

## 未来扩展

### 可能的增强

1. **更多基准选项**
   - 用户自定义基准
   - 行业指数对比

2. **参数优化建议**
   - 基于深度分析结果推荐参数调整

3. **风险预警**
   - 根据连续亏损、回撤等指标自动预警

4. **导出功能**
   - 导出分析报告（PDF/Excel）
   - 导出图表图片

5. **实时分析**
   - 实盘交易的实时深度分析
   - WebSocket 推送更新

## 贡献指南

欢迎贡献新的分析指标或改进现有实现：

1. Fork 仓库
2. 创建功能分支
3. 实现新功能/修复
4. 添加测试
5. 更新文档
6. 提交 Pull Request

## 许可证

与主项目相同的许可证。
