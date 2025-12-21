# worker 目录说明

Worker 进程池模块，提供策略代码的隔离执行环境。

## 设计目标

**核心安全改进**：主进程（API 进程）**不再执行**任何用户策略代码。
所有 `exec/compile` 操作都在隔离的 Worker 进程中进行。

## 模块结构

| 文件 | 功能 |
|------|------|
| `task_models.py` | IPC 数据模型（BacktestTask, BacktestResult, LiveTradingTask 等） |
| `worker_pool.py` | 进程池管理器，任务分发与结果收集 |
| `backtest_worker.py` | 回测任务执行器，在 Worker 进程中加载并执行用户策略 |
| `live_worker.py` | 实盘交易会话管理，在 Worker 进程中运行长期策略 |

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    API Process (Safe)                        │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐   │
│  │ API Routes  │───→│ run_backtest │───→│  WorkerPool   │   │
│  └─────────────┘    └──────────────┘    └───────┬───────┘   │
│                                                  │           │
│  ※ 主进程不执行 exec/compile 用户代码            │           │
└──────────────────────────────────────────────────┼───────────┘
                                                   │ IPC (Queue)
                                                   ▼
┌─────────────────────────────────────────────────────────────┐
│                 Worker Processes (Isolated)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Worker 1   │  │  Worker 2   │  │  Worker N   │          │
│  │  - 策略加载  │  │  - 策略加载  │  │  - 策略加载  │          │
│  │  - 回测执行  │  │  - 实盘交易  │  │  - 资源限制  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                              │
│  ※ 用户策略代码仅在此处执行                                  │
└──────────────────────────────────────────────────────────────┘
```

## 配置选项

通过环境变量配置（见 `backend/src/config/worker_config.py`）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WORKER_POOL_ENABLED` | `true` | 启用/禁用 Worker 隔离 |
| `WORKER_POOL_SIZE` | `4` | 进程池大小 |
| `WORKER_TASK_TIMEOUT` | `300` | 任务超时（秒） |
| `WORKER_MAX_MEMORY_MB` | `1024` | 每个 Worker 最大内存（MB） |

## 使用方式

Worker Pool 是默认启用的。调用 `run_backtest()` 或 `run_live()` 时：

```python
from src.service.backtest_engine import run_backtest

# 默认使用 Worker Pool（安全）
metrics = run_backtest(
    ticker="AAPL",
    strategy_name="my_strategy",
    start_date="2023-01-01",
    end_date="2023-12-31",
)

# 强制禁用 Worker Pool（仅用于开发/调试）
metrics = run_backtest(
    ticker="AAPL",
    strategy_name="my_strategy",
    start_date="2023-01-01",
    end_date="2023-12-31",
    use_worker=False,  # 不安全！
)
```

## 安全注意事项

> ⚠️ 禁用 Worker Pool (`WORKER_POOL_ENABLED=false`) 意味着用户策略代码将在 API 进程中执行。
> 这**不安全**，仅用于本地开发或完全受信任的环境。
