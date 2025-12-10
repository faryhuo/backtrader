# 快速启动指南

## 🚀 5分钟启动应用

### 第一次部署

```bash
# 1. 构建前端和安装依赖
build.bat

# 2. 启动后端服务器
cd backend
python main.py
```

### 访问应用

打开浏览器访问: **http://localhost:8000**

## 📋 配置清单

### ✅ 已完成配置

- ✅ Logto 后端应用已配置
  - Endpoint: `https://logto.fary.chat`
  - App ID: `cu32cmeb6xz49ngs9zmsy`
  - Audience: `http://localhost:8000`

- ✅ Logto 前端应用已配置
  - Endpoint: `https://logto.fary.chat`
  - App ID: `ro4uk4fd2czd7cyx3wcbm`
  - Redirect URI: `http://localhost:8000/callback`

### ⚠️ 需要在 Logto 控制台确认

访问 https://logto.fary.chat/console 并检查：

#### 1. 前端 SPA 应用 (ro4uk4fd2czd7cyx3wcbm)

**Redirect URIs** 必须包含:
```
http://localhost:8000/callback
```

**Post Logout Redirect URIs** 必须包含:
```
http://localhost:8000
```

**CORS Allowed Origins** 必须包含:
```
http://localhost:8000
```

#### 2. API Resource

确保创建了 API Resource:
- **API Identifier**: `http://localhost:8000`

#### 3. 应用关联

在前端 SPA 应用设置中:
- 进入 **API Resources** 标签
- 确保已添加 API Resource (http://localhost:8000)

## 🔄 日常开发流程

### 修改前端代码后

```bash
# 重新构建前端
cd frontend
npm run build

# 复制到后端
cd ..
powershell -Command "Copy-Item -Path 'frontend\dist\*' -Destination 'backend\resources\frontend\' -Recurse -Force"

# 刷新浏览器即可 (无需重启后端)
```

### 修改后端代码后

```bash
# 重启 Python 服务器
cd backend
# Ctrl+C 停止当前服务器
python main.py
```

## 📝 登录流程

1. 访问 `http://localhost:8000`
2. 看到登录页面，点击 **"Sign In"**
3. 跳转到 Logto 登录页面
4. 输入您的 Logto 账户凭据
5. 登录成功后自动返回应用
6. 查看右上角用户头像，确认已登录

## 🐛 常见问题

### 问题: 点击 Sign In 后跳转失败

**解决方案**:
1. 检查 Logto 控制台中的 Redirect URIs 配置
2. 确保包含 `http://localhost:8000/callback`

### 问题: 登录后返回但显示 401 错误

**解决方案**:
1. 检查 Logto 控制台中前端应用是否关联了 API Resource
2. 确认 API Resource 的 Identifier 是 `http://localhost:8000`

### 问题: 页面白屏

**解决方案**:
```bash
# 重新构建和复制
cd frontend
npm run build
cd ..
powershell -Command "Copy-Item -Path 'frontend\dist\*' -Destination 'backend\resources\frontend\' -Recurse -Force"
```

### 问题: 后端启动失败

**错误信息**: `Missing required Logto configuration`

**解决方案**:
检查 `backend/.env` 文件确保包含:
```env
LOGTO_ENDPOINT=https://logto.fary.chat
LOGTO_APP_ID=cu32cmeb6xz49ngs9zmsy
LOGTO_APP_SECRET=lrQyLj5G3r7atkHFT2rxyV1qnxSr3EBl
LOGTO_AUDIENCE=http://localhost:8000
```

## 📚 完整文档

- **详细配置**: 查看 `LOGTO_SETUP.md`
- **部署指南**: 查看 `DEPLOYMENT_GUIDE.md`
- **技术细节**: 查看 `INTEGRATION_SUMMARY.md`

## 🎯 架构说明

```
浏览器
  ↓
http://localhost:8000 (后端 FastAPI)
  ├── /           → 前端 SPA
  ├── /app        → 前端路由
  ├── /callback   → OAuth 回调
  ├── /api/*      → API 接口 (需要认证)
  └── /images/*   → 图表图片
```

所有内容由一个服务器提供！

## ⚡ 快速命令参考

```bash
# 完整构建 (首次或依赖更新后)
build.bat

# 仅构建前端
cd frontend && npm run build

# 启动后端
cd backend && python main.py

# 查看构建的前端文件
ls backend/resources/frontend

# 检查后端依赖
cd backend && pip list | grep logto
```

## ✅ 验证清单

启动后，检查以下内容：

- [ ] 访问 `http://localhost:8000` 显示登录页面
- [ ] 点击 "Sign In" 跳转到 Logto
- [ ] 登录后成功返回到应用
- [ ] 右上角显示用户头像
- [ ] 可以访问策略列表页面
- [ ] 点击用户头像可以看到邮箱和登出按钮
- [ ] 登出后返回登录页面

全部完成 ✅ 说明配置正确！

---

**需要帮助?** 查看完整文档或检查浏览器控制台的错误信息。
