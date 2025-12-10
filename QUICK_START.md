# 快速启动指南

## 🚀 5分钟快速配置

### 1. 后端配置

编辑 `backend/.env`:
```env
LOGTO_ENDPOINT=https://logto.fary.chat
LOGTO_SPA_APP_ID=ro4uk4fd2czd7cyx3wcbm
LOGTO_M2M_APP_ID=hnsx3ou27mrx1cwx3ux3i
LOGTO_M2M_APP_SECRET=upImmofjndDuad3n1IuXXrorjFnAZ4wL
LOGTO_API_RESOURCE=http://localhost:8000
```

### 2. 前端配置

编辑 `frontend/.env`:
```env
VITE_LOGTO_ENDPOINT=https://logto.fary.chat
VITE_LOGTO_APP_ID=ro4uk4fd2czd7cyx3wcbm
VITE_LOGTO_REDIRECT_URI=http://localhost:5173/callback
VITE_LOGTO_POST_LOGOUT_REDIRECT_URI=http://localhost:5173
VITE_API_RESOURCE=http://localhost:8000
```

### 3. 启动服务

```bash
# Terminal 1 - 后端
cd backend
pip install -r requirements.txt
python main.py

# Terminal 2 - 前端
cd frontend
npm install
npm run dev
```

### 4. 访问应用

打开浏览器访问: `http://localhost:5173`

## ✅ 验证清单

- [ ] 后端启动时显示 "Logto authentication initialized"
- [ ] 前端访问 `http://localhost:5173` 显示登录页面
- [ ] 点击登录后重定向到 Logto
- [ ] 登录成功后返回 `/app` 页面
- [ ] 可以正常运行回测
- [ ] 浏览器 Network 面板中 API 请求包含 `Authorization` 头

## 📖 详细文档

- **完整集成指南**: `LOGTO_INTEGRATION_GUIDE.md`
- **架构说明**: 查看集成指南第6节
- **故障排除**: 查看集成指南第7节

## 🔑 关键配置说明

### 后端 (.env)
- `LOGTO_SPA_APP_ID`: 前端 SPA 应用 ID (用于验证用户 token)
- `LOGTO_M2M_APP_ID/SECRET`: M2M 应用凭据 (可选，用于后端调用外部 API)
- `LOGTO_API_RESOURCE`: API Resource 标识符

### 前端 (.env)
- `VITE_LOGTO_APP_ID`: 使用 SPA 应用 ID (不是 M2M!)
- `VITE_API_RESOURCE`: 必须与后端的 `LOGTO_API_RESOURCE` 一致

## 🎯 认证流程

```
用户 → 登录 Logto → 获取 Token → 访问 API
                                    ↓
                        后端验证 Token → 返回数据
```

## ⚠️ 常见问题

### 401 Unauthorized
- 检查 `VITE_API_RESOURCE` 和 `LOGTO_API_RESOURCE` 是否一致
- 确保 SPA 应用已关联到 API Resource

### 无法获取 Token
- 检查 Redirect URI 配置是否正确
- 确认 CORS 设置允许前端域名

### M2M Token 失败 (可选功能)
- 验证 M2M App ID 和 Secret 正确
- 确保 M2M 应用已关联到 API Resource

---

**需要帮助？** 查看 `LOGTO_INTEGRATION_GUIDE.md` 获取完整文档
