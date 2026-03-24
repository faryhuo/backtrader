# Strategy Configuration

策略执行相关配置，包括策略文件路径、沙箱隔离和 Worker 进程池设置。

**配置文件**: `backend/resources/config/strategy_config.json`

## 配置结构

### strategy - 策略路径

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `filePath` | string | `"resources/strategy"` | 用户策略文件存储目录（相对于项目根目录） |

### sandbox - 沙箱配置

用于策略代码的安全隔离执行。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `mode` | string | `"subprocess"` | 隔离模式：`soft`（进程内）、`subprocess`（子进程）、`docker`（容器） |
| `timeoutSeconds` | float | `30.0` | 执行超时时间（秒） |
| `maxMemoryMB` | int | `512` | 最大内存限制（MB） |
| `maxCpuPercent` | int | `100` | 最大 CPU 使用率（0-100） |
| `allowNetwork` | bool | `false` | 是否允许网络访问 |
| `allowFileWrite` | bool | `false` | 是否允许文件写入 |
| `dockerImage` | string | `"python:3.11-slim"` | Docker 模式使用的镜像 |

### workerPool - Worker 进程池配置

用于回测和实盘交易的进程隔离执行。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | bool | `true` | 是否启用 Worker 池 |
| `poolSize` | int | `4` | Worker 进程数量（建议等于 CPU 核心数） |
| `taskTimeoutSeconds` | float | `300` | 单个任务超时时间（秒） |
| `maxMemoryMB` | int | `1024` | 每个 Worker 最大内存（MB） |
| `heartbeatIntervalSeconds` | float | `10` | 心跳间隔（秒） |
| `shutdownTimeoutSeconds` | float | `30` | 优雅关闭超时（秒） |
| `maxQueueSize` | int | `100` | 最大队列长度（0=无限制） |
| `allowNetwork` | bool | `true` | 是否允许网络访问（实盘交易需要） |
| `allowFileWrite` | bool | `true` | 是否允许文件写入（图表生成需要） |

## 安全说明

> [!WARNING]
> 对于多用户/公开部署环境，请参阅 `SECURITY.md`。
> - `soft` 模式不安全，仅用于开发
> - `subprocess` 模式推荐用于单用户部署
> - `docker` 模式提供最强隔离
