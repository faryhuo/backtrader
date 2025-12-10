# Backtrader 部署指南

## 架构说明

本项目采用单服务器架构：
- **后端 (FastAPI)**: 提供 API 服务 (`/api/*`) 和静态前端文件
- **前端 (React)**: 构建为静态文件，由后端提供服务
- **访问地址**: `http://localhost:8000` (开发) / `https://yourdomain.com` (生产)

```
http://localhost:8000/
  ├── /                → 前端 SPA (index.html)
  ├── /app             → 前端路由 (由 index.html 处理)
  ├── /callback        → 前端路由 (OAuth 回调)
  ├── /api/*           → 后端 API 接口
  ├── /images/*        → 生成的图表图片
  └── /assets/*        → 前端静态资源
```

## 开发环境部署

### 前置要求
- Python 3.12+
- Node.js 18+
- Logto 账户（已配置）

### 步骤 1: 安装依赖和构建

运行完整构建脚本：
```bash
build.bat
```

这会自动完成：
1. 安装 Python 后端依赖
2. 安装 Node.js 前端依赖
3. 构建前端为生产版本
4. 复制构建文件到 `backend/resources/frontend/`

### 步骤 2: 启动后端服务器

```bash
cd backend
python main.py
```

服务器将在 `http://localhost:8000` 启动

### 步骤 3: 访问应用

在浏览器打开: **`http://localhost:8000`**

您将看到登录页面，点击 "Sign In" 即可登录。

## Logto 配置

您的 Logto 已配置如下：

### 前端应用 (SPA)
- **Endpoint**: `https://logto.fary.chat`
- **App ID**: `ro4uk4fd2czd7cyx3wcbm`
- **Redirect URI**: `http://localhost:8000/callback`
- **Post Logout URI**: `http://localhost:8000`

### 后端应用 (Traditional Web)
- **Endpoint**: `https://logto.fary.chat`
- **App ID**: `cu32cmeb6xz49ngs9zmsy`
- **App Secret**: `lrQyLj5G3r7atkHFT2rxyV1qnxSr3EBl`
- **Audience**: `http://localhost:8000`

### ⚠️ Logto 控制台配置检查

确保在 Logto 控制台 (https://logto.fary.chat) 中配置：

1. **前端 SPA 应用设置**:
   - Redirect URIs: `http://localhost:8000/callback`
   - Post Logout URIs: `http://localhost:8000`
   - CORS Origins: `http://localhost:8000`

2. **API Resource 设置**:
   - API Identifier: `http://localhost:8000`
   - 确保前端应用已关联此 API Resource

## 认证流程

1. 用户访问 `http://localhost:8000`
2. 前端检测未登录 → 显示登录页面
3. 用户点击 "Sign In" → 跳转到 `https://logto.fary.chat`
4. 登录成功 → 回调到 `http://localhost:8000/callback`
5. 前端处理回调 → 获取 token → 重定向到 `/app`
6. 所有 API 请求携带 `Authorization: Bearer <token>`
7. 后端验证 token → 允许/拒绝访问

## 开发工作流

### 修改前端代码后

```bash
cd frontend
npm run build
```

然后复制构建文件：
```bash
robocopy "frontend\dist" "backend\resources\frontend" /MIR
```

或者使用完整构建脚本：
```bash
build.bat
```

### 修改后端代码后

直接重启 Python 服务器即可，无需重新构建。

## 生产环境部署

### 步骤 1: 更新环境变量

#### 后端 `.env`
```env
LOGTO_ENDPOINT=https://logto.fary.chat
LOGTO_APP_ID=<生产环境后端应用ID>
LOGTO_APP_SECRET=<生产环境后端应用密钥>
LOGTO_AUDIENCE=https://yourdomain.com
```

#### 前端构建时环境变量
创建 `frontend/.env.production`:
```env
VITE_LOGTO_ENDPOINT=https://logto.fary.chat
VITE_LOGTO_APP_ID=<生产环境前端应用ID>
VITE_LOGTO_REDIRECT_URI=https://yourdomain.com/callback
VITE_LOGTO_POST_LOGOUT_REDIRECT_URI=https://yourdomain.com
VITE_API_RESOURCE=https://yourdomain.com
```

### 步骤 2: 构建

```bash
build.bat
```

### 步骤 3: 部署

将整个 `backend/` 目录部署到服务器，包括：
- Python 代码
- `resources/frontend/` (构建的前端文件)
- `.env` 配置文件

### 步骤 4: 启动服务

```bash
cd backend
python main.py
```

或使用进程管理器（推荐）：
```bash
# 使用 systemd、supervisor 或其他进程管理工具
```

### 步骤 5: 配置反向代理

如果使用 Nginx：
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 步骤 6: 配置 HTTPS

使用 Let's Encrypt 或其他 SSL 证书：
```bash
certbot --nginx -d yourdomain.com
```

### 步骤 7: 更新 Logto 配置

在 Logto 控制台更新：
- Redirect URIs: `https://yourdomain.com/callback`
- Post Logout URIs: `https://yourdomain.com`
- CORS Origins: `https://yourdomain.com`

### 步骤 8: 更新后端 CORS

编辑 `backend/api.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 替换 "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Docker 部署 (可选)

使用现有的 Dockerfile 和 docker-compose.yml：

```bash
docker-compose up --build
```

访问 `http://localhost:8020`

## 故障排除

### 问题 1: 登录后重定向到 `/app` 但显示 404

**原因**: 前端文件未正确构建或复制

**解决方案**:
```bash
cd frontend
npm run build
robocopy "dist" "..\backend\resources\frontend" /MIR
```

### 问题 2: API 请求返回 401 Unauthorized

**原因**: Token 未正确注入或后端验证失败

**解决方案**:
1. 打开浏览器 DevTools → Network 标签
2. 检查 API 请求是否包含 `Authorization: Bearer <token>` 头
3. 检查后端日志查看 token 验证错误
4. 验证 `LOGTO_AUDIENCE` 与前端 `VITE_API_RESOURCE` 匹配

### 问题 3: 无限重定向循环

**原因**: Logto 回调 URI 配置错误

**解决方案**:
1. 检查 Logto 控制台中的 Redirect URIs 是否包含 `http://localhost:8000/callback`
2. 检查前端 `.env` 中的 `VITE_LOGTO_REDIRECT_URI` 是否正确
3. 清除浏览器缓存和 cookies

### 问题 4: CORS 错误

**原因**: CORS 配置不匹配

**解决方案**:
1. 检查 Logto 控制台中的 CORS Origins 包含 `http://localhost:8000`
2. 检查后端 `api.py` 中的 CORS 配置

### 问题 5: 前端白屏

**原因**: 前端构建失败或资源路径错误

**解决方案**:
```bash
# 重新构建
cd frontend
npm run build

# 检查构建输出
ls dist/

# 确保文件复制到正确位置
robocopy "dist" "..\backend\resources\frontend" /MIR
```

## 日常维护

### 更新依赖

后端：
```bash
cd backend
pip install --upgrade -r requirements.txt
```

前端：
```bash
cd frontend
npm update
```

### 查看日志

后端日志会输出到控制台，建议使用进程管理器捕获：
```bash
python main.py > app.log 2>&1
```

### 备份

需要备份的内容：
- `backend/.env` - 环境配置
- `backend/strategy/` - 用户策略文件
- 数据库（如果使用）

## 性能优化

### 1. 启用 Gzip 压缩

在 Nginx 配置中：
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

### 2. 缓存静态文件

```nginx
location /assets/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. 使用 CDN

将 `/assets/` 和 `/images/` 上传到 CDN。

## 安全建议

1. ✅ 始终使用 HTTPS (生产环境)
2. ✅ 限制 CORS 来源（不使用 `*`）
3. ✅ 定期更新依赖
4. ✅ 不要在代码中硬编码密钥
5. ✅ 使用环境变量管理敏感信息
6. ✅ 设置合理的 token 过期时间
7. ✅ 实施速率限制（防止 DDoS）
8. ✅ 定期审查 Logto 访问日志

## 监控

建议监控以下指标：
- API 响应时间
- 认证成功/失败率
- 错误日志
- 服务器资源使用（CPU、内存）

## 支持

如有问题，请检查：
1. 本文档的故障排除部分
2. `LOGTO_SETUP.md` 详细配置指南
3. `INTEGRATION_SUMMARY.md` 技术细节
4. Logto 官方文档: https://docs.logto.io

---

**最后更新**: 2025-12-10
**适用版本**: Logto React SDK v4.0.9, Logto Python SDK v0.2.1
