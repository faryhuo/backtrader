# Docker环境配置

<cite>
**本文档引用的文件**
- [Dockerfile](file://Dockerfile)
- [docker-compose.yml](file://docker-compose.yml)
- [docker-build-optimized.sh](file://docker-build-optimized.sh)
- [backend/.env.prod](file://backend/.env.prod)
- [backend/.env.template](file://backend/.env.template)
- [backend/main.py](file://backend/main.py)
- [backend/api.py](file://backend/api.py)
</cite>

## 目录
1. [简介](#简介)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构概述](#架构概述)
5. [详细组件分析](#详细组件分析)
6. [依赖分析](#依赖分析)
7. [性能考虑](#性能考虑)
8. [故障排除指南](#故障排除指南)
9. [结论](#结论)

## 简介
本文档详细说明了基于Docker的容器化部署配置方案，涵盖Dockerfile构建阶段、依赖安装、入口点设置，以及docker-compose.yml中各服务的配置项。同时解析了构建优化脚本的策略，并提供不同部署场景下的配置建议。

## 项目结构
本项目采用前后端分离的架构，包含后端服务、前端界面和Docker容器化配置。主要目录结构包括backend（后端服务）、frontend（前端应用）和根目录下的Docker相关配置文件。

```mermaid
graph TD
A[项目根目录] --> B[Dockerfile]
A --> C[docker-compose.yml]
A --> D[docker-build-optimized.sh]
A --> E[backend]
A --> F[frontend]
E --> G[main.py]
E --> H[api.py]
E --> I[.env.prod]
E --> J[.env.template]
F --> K[package.json]
```

**Diagram sources**
- [Dockerfile](file://Dockerfile#L1-L78)
- [docker-compose.yml](file://docker-compose.yml#L1-L12)
- [backend/main.py](file://backend/main.py#L1-L21)

**Section sources**
- [Dockerfile](file://Dockerfile#L1-L78)
- [docker-compose.yml](file://docker-compose.yml#L1-L12)

## 核心组件
系统核心组件包括后端API服务、前端用户界面和Docker容器化部署配置。后端基于FastAPI框架构建，通过Daphne服务器处理WebSocket连接，前端使用React技术栈。

**Section sources**
- [backend/main.py](file://backend/main.py#L1-L21)
- [backend/api.py](file://backend/api.py#L1-L4)
- [frontend/package.json](file://frontend/package.json#L1-L40)

## 架构概述
系统采用微服务架构，通过Docker容器化部署。后端服务处理业务逻辑和数据存储，前端提供用户界面，两者通过API进行通信。

```mermaid
graph LR
subgraph "Docker容器"
A[后端服务]
B[前端服务]
C[数据库]
end
D[客户端浏览器] --> B
B --> A
A --> C
A --> |WebSocket| D
```

**Diagram sources**
- [docker-compose.yml](file://docker-compose.yml#L1-L12)
- [Dockerfile](file://Dockerfile#L1-L78)

## 详细组件分析

### Dockerfile构建分析
Dockerfile采用多阶段构建策略，分为构建阶段和运行阶段，优化了镜像大小和构建效率。

#### 构建阶段分析
```mermaid
classDiagram
class BuilderStage {
+使用python : 3.12-slim-bookworm基础镜像
+安装编译依赖包
+使用阿里云镜像加速下载
+预构建Python依赖轮子包
}
class RuntimeStage {
+使用轻量级运行时镜像
+仅安装运行时库
+复制预构建的轮子包
+安装依赖避免编译
+复制应用代码
+配置环境变量
+设置启动命令
}
BuilderStage --> RuntimeStage : 复制预构建轮子包
```

**Diagram sources**
- [Dockerfile](file://Dockerfile#L1-L31)
- [Dockerfile](file://Dockerfile#L32-L78)

#### 多阶段构建流程
```mermaid
flowchart TD
Start([开始构建]) --> BuilderStage["构建阶段: 预编译依赖"]
BuilderStage --> InstallBuildDeps["安装编译依赖"]
InstallBuildDeps --> CopyRequirements["复制requirements.txt"]
CopyRequirements --> BuildWheels["构建Python轮子包"]
BuildWheels --> RuntimeStage["运行阶段: 创建最终镜像"]
RuntimeStage --> InstallRuntimeLibs["安装运行时库"]
InstallRuntimeLibs --> CopyWheels["复制预构建轮子包"]
CopyWheels --> InstallFromWheels["从轮子包安装依赖"]
InstallFromWheels --> CopyAppCode["复制应用代码"]
CopyAppCode --> SetupEnv["设置环境变量"]
SetupEnv --> DefineCMD["定义启动命令"]
DefineCMD --> End([镜像构建完成])
```

**Diagram sources**
- [Dockerfile](file://Dockerfile#L1-L78)

**Section sources**
- [Dockerfile](file://Dockerfile#L1-L78)
- [backend/requirements.txt](file://backend/requirements.txt)

### docker-compose配置分析
docker-compose.yml文件定义了服务的容器化部署配置，包括端口映射、环境变量等。

#### 服务配置项分析
```mermaid
erDiagram
SERVICE_APP {
string service_name PK
string build_context
string port_mapping
string environment_variables
string restart_policy
}
SERVICE_APP ||--o{ PORT_MAPPING : "包含"
SERVICE_APP ||--o{ ENVIRONMENT : "包含"
PORT_MAPPING {
string host_port PK
string container_port
}
ENVIRONMENT {
string variable_name PK
string variable_value
}
```

**Diagram sources**
- [docker-compose.yml](file://docker-compose.yml#L1-L12)

#### 服务启动流程
```mermaid
sequenceDiagram
participant User as "用户"
participant DockerCompose as "Docker Compose"
participant Builder as "构建器"
participant Container as "容器实例"
User->>DockerCompose : 执行 docker-compose up
DockerCompose->>Builder : 构建镜像 (基于Dockerfile)
Builder->>Builder : 执行多阶段构建
Builder-->>DockerCompose : 镜像构建完成
DockerCompose->>Container : 创建并启动容器
Container->>Container : 设置环境变量
Container->>Container : 映射端口 8020 : 8000
Container->>Container : 执行启动命令 python main.py
Container-->>User : 服务运行在 0.0.0.0 : 8020
```

**Diagram sources**
- [docker-compose.yml](file://docker-compose.yml#L1-L12)
- [Dockerfile](file://Dockerfile#L77-L78)
- [backend/main.py](file://backend/main.py#L1-L21)

**Section sources**
- [docker-compose.yml](file://docker-compose.yml#L1-L12)

### 构建优化脚本分析
docker-build-optimized.sh脚本提供了优化的Docker构建流程，特别适合网络环境较差的场景。

#### 构建优化策略
```mermaid
flowchart TD
A[开始优化构建] --> B[启用BuildKit]
B --> C[启用构建缓存]
C --> D[设置构建参数]
D --> E[指定Dockerfile]
E --> F[执行构建命令]
F --> G{构建成功?}
G --> |是| H[显示成功信息]
G --> |否| I[显示错误信息]
H --> J[显示运行指令]
I --> K[退出脚本]
```

**Diagram sources**
- [docker-build-optimized.sh](file://docker-build-optimized.sh#L1-L28)

#### 环境变量配置
```mermaid
classDiagram
class EnvConfig {
+HOST : 0.0.0.0
+PORT : 8000
+LOGTO_ISSUER : 认证服务器地址
+LOGTO_JWKS_URI : JWKS端点
+LOGTO_AUDIENCE : 受众标识
+OPENAI_API_KEY : OpenAI API密钥
+OPENAI_BASE_URL : OpenAI基础URL
+DATABASE_URL : 数据库连接字符串
+LIVE_TRADING_ENABLED : 实盘交易开关
+DEFAULT_EXCHANGE : 默认交易所
+DEFAULT_TRADE_MODE : 默认交易模式
}
class EnvTypes {
+.env.prod : 生产环境配置
+.env.template : 配置模板
}
EnvTypes --> EnvConfig : "定义"
```

**Diagram sources**
- [backend/.env.prod](file://backend/.env.prod#L1-L15)
- [backend/.env.template](file://backend/.env.template#L1-L86)

**Section sources**
- [backend/.env.prod](file://backend/.env.prod#L1-L15)
- [backend/.env.template](file://backend/.env.template#L1-L86)

## 依赖分析
系统依赖关系清晰，采用分层架构设计，各组件间耦合度低。

```mermaid
graph TD
A[Docker容器] --> B[Python运行时]
B --> C[FastAPI框架]
C --> D[Daphne服务器]
D --> E[WebSocket支持]
C --> F[业务路由]
F --> G[数据库模块]
F --> H[交易引擎]
F --> I[策略管理]
G --> J[数据存储]
H --> K[实时交易]
I --> L[策略回测]
```

**Diagram sources**
- [Dockerfile](file://Dockerfile#L1-L78)
- [backend/main.py](file://backend/main.py#L1-L21)
- [backend/requirements.txt](file://backend/requirements.txt)

**Section sources**
- [Dockerfile](file://Dockerfile#L1-L78)
- [backend/requirements.txt](file://backend/requirements.txt)

## 性能考虑
容器化部署方案充分考虑了性能优化，通过多阶段构建、依赖缓存等策略提升构建和运行效率。

**Section sources**
- [Dockerfile](file://Dockerfile#L1-L78)
- [docker-build-optimized.sh](file://docker-build-optimized.sh#L1-L28)

## 故障排除指南
当遇到容器化部署问题时，可参考以下常见问题的解决方案。

**Section sources**
- [docker-build-optimized.sh](file://docker-build-optimized.sh#L1-L28)
- [docker-compose.yml](file://docker-compose.yml#L1-L12)

## 结论
本文档详细解析了项目的Docker容器化部署方案，包括多阶段构建、服务配置、环境变量管理等关键方面。该方案具有良好的可维护性和扩展性，适合开发和生产环境部署。