# Logto 前后端集成配置指南

本指南说明如何配置 Logto 实现前端 SPA 应用与后端的集成认证。

## 架构概述

```
┌─────────────────────────────────────────────────────────────────┐
│                     浏览器 (Frontend SPA)                        │
│                                                                  │
│  1. 用户访问应用                                                  │
│  2. Logto SDK 引导用户登录                                        │
│  3. 获取 Access Token                                            │
│  4. API 请求携带 Bearer Token                                     │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           │ HTTP + Authorization: Bearer <token>
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│                                                                  │
│  1. 接收带 Bearer Token 的请求                                    │
│  2. 验证 JWT Token (签名、过期时间、audience)                      │
│  3. 从 Token 提取用户信息                                          │
│  4. 执行业务逻辑并返回数据                                          │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           │ JWKS 验证
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Logto (https://logto.fary.chat)                │
│                                                                  │
│  - 提供用户登录界面                                                │
│  - 颁发 JWT Access Token                                         │
│  - 提供 JWKS 用于 Token 验证                                      │
└─────────────────────────────────────────────────────────────────┘
```

## 前提条件

1. Logto 账户 (cloud.logto.io 或自建)
2. Node.js 18+
3. Python 3.12+

## 第一步：在 Logto Console 创建应用

### 1.1 创建 API Resource

1. 进入 Logto Console → **API Resources**
2. 点击 **Create API Resource**
3. 配置:
   - **Name**: `Backtrader API`
   - **API Identifier**: `http://localhost:8000` (开发环境)
4. 保存 **API Identifier**

### 1.2 创建 SPA 应用 (前端)

1. 进入 Logto Console → **Applications**
2. 点击 **Create Application**
3. 选择 **Single Page Application**
4. 配置:
   - **Application Name**: `Backtrader Frontend`
   - **Redirect URIs**:
     - 开发: `http://localhost:5173/callback`
   - **Post Logout Redirect URIs**:
     - 开发: `http://localhost:5173`
   - **CORS Allowed Origins**:
     - 开发: `http://localhost:5173`
5. 保存并记录:
   - **App ID**: `ro4uk4fd2czd7cyx3wcbm`

### 1.3 关联 SPA 应用到 API Resource

1. 在 SPA 应用设置页面
2. 进入 **API Resources** 标签
3. 点击 **Add API Resource**
4. 选择 `Backtrader API`
5. 保存

### 1.4 创建 M2M 应用 (可选，用于后端调用外部 API)

如果后端需要调用其他受保护的 API：

1. 进入 Logto Console → **Applications**
2. 点击 **Create Application**
3. 选择 **Machine-to-Machine**
4. 配置:
   - **Application Name**: `Backtrader Backend M2M`
5. 保存并记录:
   - **App ID**: `hnsx3ou27mrx1cwx3ux3i`
   - **App Secret**: `upImmofjndDuad3n1IuXXrorjFnAZ4wL`
6. 关联到 API Resource

## 第二步：配置后端

### 2.1 更新环境变量

编辑 `backend/.env`:

```env
# OpenAI Configuration
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

**说明:**
- `LOGTO_SPA_APP_ID`: 前端 SPA 应用的 ID (必需)
- `LOGTO_M2M_APP_ID/SECRET`: 后端 M2M 应用凭证 (可选，仅在需要调用外部 API 时使用)
- `LOGTO_API_RESOURCE`: API 资源标识符，必须与 Logto Console 中的一致

### 2.2 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

主要依赖:
- `python-jose[cryptography]` - JWT 验证
- `requests` - HTTP 客户端

### 2.3 启动后端

```bash
cd backend
python main.py
```

预期输出:
```
Logto authentication initialized: https://logto.fary.chat
  - SPA App ID: ro4uk4fd2czd7cyx3wcbm
  - API Resource: http://localhost:8000
  - M2M App ID: hnsx3ou27mrx1cwx3ux3i
  - M2M authentication enabled for backend-to-backend calls
User authentication is ready!
```

## 第三步：配置前端

### 3.1 更新环境变量

前端 `frontend/.env` 已配置:

```env
# Logto Authentication Configuration (Development)
VITE_LOGTO_ENDPOINT=https://logto.fary.chat
VITE_LOGTO_APP_ID=ro4uk4fd2czd7cyx3wcbm
VITE_LOGTO_REDIRECT_URI=http://localhost:5173/callback
VITE_LOGTO_POST_LOGOUT_REDIRECT_URI=http://localhost:5173
VITE_API_RESOURCE=http://localhost:8000
```

**重要:** `VITE_API_RESOURCE` 必须与后端的 `LOGTO_API_RESOURCE` 一致！

### 3.2 安装依赖

```bash
cd frontend
npm install
```

主要依赖:
- `@logto/react` - Logto React SDK

### 3.3 启动前端

```bash
cd frontend
npm run dev
```

前端将在 `http://localhost:5173` 启动

## 第四步：测试认证流程

### 4.1 测试登录

1. 打开浏览器访问 `http://localhost:5173`
2. 应该看到登录页面
3. 点击 **Sign In**
4. 重定向到 Logto 登录页
5. 输入凭证登录
6. 认证成功后重定向回 `/callback`
7. 然后自动跳转到 `/app` (主应用)

### 4.2 测试 API 调用

1. 打开浏览器 DevTools → Network 标签
2. 在应用中执行操作 (如获取策略列表)
3. 查看 API 请求:
   ```
   Request URL: http://localhost:8000/api/strategies
   Request Headers:
     Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
4. 应该返回 `200 OK` 和数据

### 4.3 测试登出

1. 点击右上角用户头像
2. 点击 **Logout**
3. 应该重定向回首页 `/`
4. 尝试直接访问 `/app` 会重定向到登录页

### 4.4 测试未认证访问

新开隐身窗口:
```bash
# 直接访问 API (无 token)
curl http://localhost:8000/api/strategies
```

应该返回:
```json
{
  "detail": "Not authenticated"
}
```

## 认证流程详解

### 用户登录流程

```
1. 用户访问 http://localhost:5173
   ↓
2. App 检测未登录 → 显示登录页
   ↓
3. 用户点击 "Sign In"
   ↓
4. Logto SDK 重定向到 Logto 登录页
   URL: https://logto.fary.chat/oidc/auth?client_id=...&redirect_uri=...
   ↓
5. 用户输入用户名/密码
   ↓
6. Logto 验证成功 → 重定向回应用
   URL: http://localhost:5173/callback?code=...
   ↓
7. Callback 页面用 code 换取 tokens
   POST https://logto.fary.chat/oidc/token
   Response: { access_token, refresh_token, id_token }
   ↓
8. Logto SDK 存储 tokens (内存 + sessionStorage)
   ↓
9. 重定向到 /app
   ↓
10. 应用可以正常使用
```

### API 请求流程

```
1. 前端调用 API
   api.getStrategies()
   ↓
2. api.js 中的 buildRequest()
   ↓
3. 调用 getAccessToken(resource) 获取 token
   ↓
4. 添加 Authorization header
   headers.set('Authorization', `Bearer ${token}`)
   ↓
5. 发送请求到后端
   GET http://localhost:8000/api/strategies
   ↓
6. 后端接收请求
   @router.get("/strategies")
   def get_strategy_list(user: dict = Depends(get_current_user))
   ↓
7. get_current_user 依赖执行
   ↓
8. 从 header 提取 token
   ↓
9. 从 Logto 获取 JWKS (缓存)
   ↓
10. 验证 token (签名、过期时间、audience、issuer)
    ↓
11. 提取用户信息 (sub, email, etc.)
    ↓
12. 执行业务逻辑
    ↓
13. 返回数据
```

## Token 管理

### Access Token
- **用途**: API 认证
- **有效期**: 默认 1 小时
- **存储**: 内存 + sessionStorage (Logto SDK 管理)
- **刷新**: SDK 自动使用 refresh token 刷新

### Refresh Token
- **用途**: 获取新的 access token
- **有效期**: 默认 14 天
- **存储**: sessionStorage (仅限)

### ID Token
- **用途**: 用户身份信息
- **包含**: email, name, username 等
- **使用**: 显示用户信息 (如头像下拉菜单)

## 代码结构

### 前端关键文件

**`frontend/src/App.jsx`**
```javascript
// 使用 LogtoProvider 包装应用
<LogtoProvider>
  <BrowserRouter>
    <AppContent />
  </BrowserRouter>
</LogtoProvider>

// 设置 token getter
useEffect(() => {
  setTokenGetter(getAccessToken)
}, [getAccessToken])
```

**`frontend/src/services/api.js`**
```javascript
// API 请求前注入 token
const token = await getTokenFn(resource)
headers.set('Authorization', `Bearer ${token}`)
```

**`frontend/src/providers/LogtoProvider.jsx`**
```javascript
// Logto 配置
const config = {
  endpoint: import.meta.env.VITE_LOGTO_ENDPOINT,
  appId: import.meta.env.VITE_LOGTO_APP_ID,
  resources: [import.meta.env.VITE_API_RESOURCE],
}
```

### 后端关键文件

**`backend/auth.py`**
```python
# 用户 token 验证
async def get_current_user(credentials: HTTPAuthorizationCredentials):
    token = credentials.credentials
    config = get_logto_config()
    user_claims = verify_user_token(token, config)
    return user_claims

# M2M token 获取 (可选)
async def get_m2m_token():
    config = get_logto_config()
    return obtain_m2m_token(config)
```

**`backend/routes/api_routes.py`**
```python
# 保护的 API 端点
@router.get("/strategies")
def get_strategy_list(user: dict = Depends(get_current_user)):
    # user 包含: sub, email, aud, iss, exp, iat
    names = list_strategies()
    return {"strategies": names}
```

## 生产环境部署

### 1. 更新 Logto Console 配置

添加生产环境 URL:
- Redirect URIs: `https://yourdomain.com/callback`
- Post Logout URIs: `https://yourdomain.com`
- CORS Origins: `https://yourdomain.com`

### 2. 更新环境变量

**Backend `.env`:**
```env
LOGTO_API_RESOURCE=https://yourdomain.com
```

**Frontend `.env.production`:**
```env
VITE_LOGTO_REDIRECT_URI=https://yourdomain.com/callback
VITE_LOGTO_POST_LOGOUT_REDIRECT_URI=https://yourdomain.com
VITE_API_RESOURCE=https://yourdomain.com
```

### 3. 更新 CORS 设置

`backend/api.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 限制为生产域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. 启用 HTTPS

⚠️ **必须使用 HTTPS**，否则 token 传输不安全！

## 故障排查

### 问题: "401 Unauthorized"

**解决方案:**
1. 检查前端是否成功获取 token (浏览器控制台)
2. 检查 `VITE_API_RESOURCE` 是否与后端 `LOGTO_API_RESOURCE` 一致
3. 检查 token 是否过期
4. 查看后端日志中的 token 验证错误

### 问题: "Failed to get access token"

**解决方案:**
1. 检查 SPA 应用是否关联了 API Resource
2. 检查 `VITE_API_RESOURCE` 配置是否正确
3. 清除浏览器缓存和 sessionStorage

### 问题: 登录后无限重定向

**解决方案:**
1. 检查 `VITE_LOGTO_REDIRECT_URI` 是否与 Logto Console 中配置一致
2. 检查 `/callback` 路由是否为公开路由 (不需要认证)
3. 清除浏览器缓存

### 问题: CORS 错误

**解决方案:**
1. 检查 Logto Console 中 CORS Allowed Origins 是否包含前端 URL
2. 检查后端 `api.py` 中 CORS 配置
3. 确保前端和后端端口正确

## M2M 认证使用 (可选)

如果后端需要调用外部保护的 API:

```python
from fastapi import APIRouter, Depends
from auth import get_m2m_token
import requests

router = APIRouter()

@router.get("/api/external-data")
async def fetch_external_data(m2m_token: str = Depends(get_m2m_token)):
    """使用 M2M token 调用外部 API"""
    headers = {"Authorization": f"Bearer {m2m_token}"}
    response = requests.get(
        "https://external-api.example.com/data",
        headers=headers
    )
    return response.json()
```

## 安全最佳实践

1. ✅ **始终使用 HTTPS** (生产环境)
2. ✅ **限制 CORS origins** 到特定域名
3. ✅ **验证所有 API 端点** (使用 `Depends(get_current_user)`)
4. ✅ **不要在前端存储敏感信息** (App Secret 只在后端)
5. ✅ **定期轮换 M2M credentials**
6. ✅ **监控异常认证请求**
7. ✅ **设置合理的 token 过期时间**

## 相关资源

- [Logto 官方文档](https://docs.logto.io)
- [Logto React SDK](https://docs.logto.io/sdk/react/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io) - JWT 解码工具

## 常见问题

**Q: 前端和后端必须在同一域名下吗？**
A: 不需要，但需要配置正确的 CORS 和 API Resource URL。

**Q: 可以关闭 M2M 功能吗？**
A: 可以，M2M 是可选的。如果不配置 `LOGTO_M2M_APP_ID`，系统仍然正常工作。

**Q: Token 过期后会怎样？**
A: Logto SDK 会自动使用 refresh token 刷新 access token，用户无感知。

**Q: 如何获取当前用户信息？**
A: 在 API 端点中使用 `user: dict = Depends(get_current_user)`，user 对象包含 `sub` (用户ID)、`email` 等信息。

**Q: 能否在后端直接登录用户？**
A: 不能。用户必须通过前端的 OAuth 流程登录，后端只负责验证 token。

## 总结

本配置实现了:
- ✅ 前端用户通过 Logto 登录
- ✅ 前端 API 请求携带 JWT token
- ✅ 后端验证 token 并保护 API 端点
- ✅ 可选的后端 M2M 认证 (调用外部 API)
- ✅ 完整的用户会话管理
- ✅ 自动 token 刷新

现在您的应用已经具备了完整的认证系统！
