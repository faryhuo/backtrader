# Logto 集成指南 (用户认证 + M2M)

本指南说明如何配置 Logto 进行**前端用户认证**和**后端M2M认证**的混合集成。

## 架构概述

```
┌─────────────────────────────────────────────────────────────────┐
│                    前端 (React SPA)                              │
│                                                                  │
│  • 用户通过 Logto 登录                                           │
│  • 获取 JWT Access Token                                        │
│  • 在 API 请求中发送 Bearer Token                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP + Bearer Token
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    后端 (FastAPI)                                │
│                                                                  │
│  • 验证前端发来的用户 Token                                      │
│  • 保护所有 /api/* 端点                                          │
│  • (可选) 使用 M2M Token 调用外部 API                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Token 验证 & M2M Token获取
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Logto 服务器                                  │
│                                                                  │
│  • SPA 应用 (前端用户登录)                                       │
│  • M2M 应用 (后端服务调用)                                       │
│  • API Resource (受保护的 API)                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 1. Logto 控制台配置

### 1.1 创建 API Resource

1. 进入 Logto 控制台 → **API Resources**
2. 点击 **Create API Resource**
3. 配置：
   - **Name**: `Backtrader API`
   - **API Identifier**: `http://localhost:8000` (开发环境)
4. 保存 **API Identifier**，后续配置需要使用

### 1.2 创建 SPA 应用 (前端用户认证)

1. 进入 **Applications** → **Create Application**
2. 选择 **Single Page App**
3. 配置：
   - **Application Name**: `Backtrader Frontend`
   - **Redirect URIs**:
     - 开发环境: `http://localhost:5173/callback`
     - 生产环境: `https://yourdomain.com/callback`
   - **Post Logout Redirect URIs**:
     - 开发环境: `http://localhost:5173`
     - 生产环境: `https://yourdomain.com`
   - **CORS Allowed Origins**:
     - 开发环境: `http://localhost:5173`
4. 保存 **App ID** (例如: `ro4uk4fd2czd7cyx3wcbm`)
5. 进入 **API Resources** 标签
6. 将 SPA 应用关联到 `Backtrader API`

### 1.3 创建 M2M 应用 (后端服务认证，可选)

1. 进入 **Applications** → **Create Application**
2. 选择 **Machine-to-Machine**
3. 配置:
   - **Application Name**: `Backtrader M2M`
4. 保存 **App ID** 和 **App Secret**:
   - App ID: `hnsx3ou27mrx1cwx3ux3i`
   - App Secret: `upImmofjndDuad3n1IuXXrorjFnAZ4wL`
5. 进入 **API Resources** 标签
6. 将 M2M 应用关联到需要调用的 API Resource

## 2. 后端配置

### 2.1 环境变量配置

编辑 `backend/.env`:

```env
OPENAI_API_KEY=your-openai-key
OPENAI_BASE_URL=https://api.gptgod.online/v1/

# Logto Authentication Configuration
LOGTO_ENDPOINT=https://logto.fary.chat

# User Authentication (SPA Frontend App)
LOGTO_SPA_APP_ID=ro4uk4fd2czd7cyx3wcbm

# M2M Authentication (Backend-to-Backend, Optional)
LOGTO_M2M_APP_ID=hnsx3ou27mrx1cwx3ux3i
LOGTO_M2M_APP_SECRET=upImmofjndDuad3n1IuXXrorjFnAZ4wL

# API Resource
LOGTO_API_RESOURCE=http://localhost:8000
```

**说明：**
- `LOGTO_SPA_APP_ID`: 前端 SPA 应用的 ID (必需)
- `LOGTO_M2M_APP_ID/SECRET`: M2M 应用凭据 (可选，仅在需要调用外部API时使用)
- `LOGTO_API_RESOURCE`: API Resource 标识符，必须与 Logto 控制台中配置的一致

### 2.2 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2.3 启动后端

```bash
cd backend
python main.py
```

应该看到：
```
Logto authentication initialized: https://logto.fary.chat
  - SPA App ID: ro4uk4fd2czd7cyx3wcbm
  - API Resource: http://localhost:8000
  - M2M App ID: hnsx3ou27mrx1cwx3ux3i
  - M2M authentication enabled for backend-to-backend calls
User authentication is ready!
```

## 3. 前端配置

### 3.1 环境变量配置

编辑 `frontend/.env`:

```env
# Logto Authentication Configuration (Development)
VITE_LOGTO_ENDPOINT=https://logto.fary.chat
VITE_LOGTO_APP_ID=ro4uk4fd2czd7cyx3wcbm
VITE_LOGTO_REDIRECT_URI=http://localhost:5173/callback
VITE_LOGTO_POST_LOGOUT_REDIRECT_URI=http://localhost:5173
VITE_API_RESOURCE=http://localhost:8000
```

**说明：**
- `VITE_LOGTO_APP_ID`: 使用 SPA 应用的 App ID (不是 M2M 的!)
- `VITE_API_RESOURCE`: 必须与后端的 `LOGTO_API_RESOURCE` 一致

### 3.2 安装依赖

```bash
cd frontend
npm install
```

### 3.3 启动前端

```bash
cd frontend
npm run dev
```

前端应该启动在 `http://localhost:5173`

## 4. 认证流程

### 4.1 用户登录流程

```
1. 用户访问 http://localhost:5173
   ↓
2. 重定向到 /（登录页面）
   ↓
3. 点击 "Sign In"
   ↓
4. 重定向到 Logto 登录页面
   ↓
5. 用户输入凭据
   ↓
6. Logto 重定向回 /callback?code=...
   ↓
7. 前端交换 code 获取 access_token
   ↓
8. 存储 token 并重定向到 /app
   ↓
9. 所有 API 请求自动附带: Authorization: Bearer <token>
   ↓
10. 后端验证 token 并返回数据
```

### 4.2 M2M 认证流程 (可选)

```
1. 后端需要调用外部受保护 API
   ↓
2. 使用 Depends(get_m2m_token) 获取 M2M token
   ↓
3. 后端向 Logto 请求 token (client_credentials flow)
   ↓
4. Logto 验证 M2M 凭据并返回 token
   ↓
5. 后端缓存 token (有效期约1小时)
   ↓
6. 后端使用 token 调用外部 API
```

## 5. 代码示例

### 5.1 前端 - API 调用 (自动注入 token)

```javascript
// frontend/src/services/api.js
import { api } from './services/api'

// Token 由 LogtoProvider 自动注入
const strategies = await api.getStrategies()
```

### 5.2 后端 - 验证用户 token

```python
# backend/routes/api_routes.py
from fastapi import Depends
from auth import get_current_user

@router.get("/strategies")
def get_strategy_list(user: dict = Depends(get_current_user)) -> dict:
    # user 包含 token 的 claims (sub, email, etc.)
    names = list_strategies()
    return {"strategies": names}
```

### 5.3 后端 - 使用 M2M token 调用外部 API (可选)

```python
# 示例：调用需要认证的外部 API
from fastapi import Depends
from auth import get_m2m_token
import requests

@router.get("/external-data")
async def fetch_external_data(m2m_token: str = Depends(get_m2m_token)):
    headers = {"Authorization": f"Bearer {m2m_token}"}
    response = requests.get(
        "https://external-api.example.com/data",
        headers=headers
    )
    return response.json()
```

## 6. 测试

### 6.1 测试用户登录

1. 打开 `http://localhost:5173`
2. 点击 "Sign In"
3. 使用测试账户登录
4. 登录成功后应重定向到 `/app`
5. 打开浏览器 DevTools → Network
6. 查看 API 请求，应该包含 `Authorization: Bearer ...` 头

### 6.2 测试 API 认证

```bash
# 无 token - 应该返回 401
curl http://localhost:8000/api/strategies

# 有效 token - 应该返回 200
curl http://localhost:8000/api/strategies \
  -H "Authorization: Bearer <your-token>"
```

## 7. 常见问题

### 问题: 前端无法获取 access token

**解决方案:**
1. 检查 `VITE_API_RESOURCE` 是否与后端 `LOGTO_API_RESOURCE` 一致
2. 确保 SPA 应用已关联到 API Resource
3. 检查浏览器控制台错误信息

### 问题: 后端返回 401 Unauthorized

**解决方案:**
1. 检查前端是否成功获取并发送 token
2. 验证 `LOGTO_SPA_APP_ID` 配置正确
3. 确认 `LOGTO_API_RESOURCE` 匹配
4. 查看后端日志中的具体错误

### 问题: M2M token 获取失败

**解决方案:**
1. 验证 `LOGTO_M2M_APP_ID` 和 `LOGTO_M2M_APP_SECRET` 正确
2. 确保 M2M 应用已关联到 API Resource
3. 检查网络连接到 Logto endpoint

## 8. 生产部署

### 8.1 更新环境变量

**后端 `.env`:**
```env
LOGTO_API_RESOURCE=https://yourdomain.com
```

**前端 `.env.production`:**
```env
VITE_LOGTO_REDIRECT_URI=https://yourdomain.com/callback
VITE_LOGTO_POST_LOGOUT_REDIRECT_URI=https://yourdomain.com
VITE_API_RESOURCE=https://yourdomain.com
```

### 8.2 更新 Logto 控制台

1. 在 SPA 应用设置中添加生产环境 URIs
2. 更新 CORS Allowed Origins

### 8.3 CORS 配置

编辑 `backend/api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 替换通配符
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 9. 认证架构总结

### 认证模式对比

| 功能 | 用户认证 (SPA) | M2M 认证 |
|------|----------------|----------|
| 用途 | 前端用户登录 | 后端服务间调用 |
| 认证流程 | Authorization Code | Client Credentials |
| Token 持有者 | 前端浏览器 | 后端服务器 |
| Token 用途 | 访问 API | 调用外部 API |
| 配置 | 必需 | 可选 |
| App ID | `LOGTO_SPA_APP_ID` | `LOGTO_M2M_APP_ID` |
| Secret | 无 (公开应用) | `LOGTO_M2M_APP_SECRET` |

### 文件结构

```
backend/
├── .env                         # 环境配置 (SPA + M2M)
├── auth.py                      # 统一认证模块
│   ├── LogtoConfig              # 配置类
│   ├── verify_user_token()      # 验证用户 token
│   ├── obtain_m2m_token()       # 获取 M2M token
│   ├── get_current_user()       # FastAPI 依赖
│   └── get_m2m_token()          # FastAPI 依赖
├── routes/
│   ├── api_routes.py            # 受保护的 API (需要用户 token)
│   └── ai_routes.py             # AI 分析 API (需要用户 token)
└── api.py                       # FastAPI 应用

frontend/
├── .env                         # 环境配置 (SPA)
├── src/
│   ├── providers/
│   │   └── LogtoProvider.jsx   # Logto React Provider
│   ├── services/
│   │   └── api.js              # API 客户端 (自动注入 token)
│   └── App.jsx                 # 应用入口 (含认证)
```

## 10. 相关资源

- [Logto 文档](https://docs.logto.io)
- [Logto React SDK](https://docs.logto.io/sdk/react/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OAuth 2.0 规范](https://oauth.net/2/)

---

**最后更新**: 2025-12-10
**集成模式**: 用户认证 (SPA) + M2M 认证 (可选)
