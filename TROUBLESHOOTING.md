# 故障排除指南 - 重定向循环问题

## 核心问题：重定向循环

如果您访问 `http://localhost:8000` 一直在重定向，请按照以下步骤操作：

### 🔧 关键配置检查

**最常见的问题**: `LOGTO_AUDIENCE` 和 `VITE_API_RESOURCE` 必须完全一致！

#### 1. 检查后端配置

打开 `backend/.env`，确保：
```env
LOGTO_AUDIENCE=http://localhost:8000
```

⚠️ **不能是** `http://localhost:8000/api`

#### 2. 检查前端配置

打开 `frontend/.env`，确保：
```env
VITE_API_RESOURCE=http://localhost:8000
```

⚠️ **不能是** `http://localhost:8000/api`

### 🔄 修复步骤

1. 修正配置文件（如上）
2. 重新构建前端：
   ```bash
   cd frontend
   npm run build
   ```
3. 复制到后端：
   ```bash
   powershell -Command "Copy-Item -Path 'frontend\dist\*' -Destination 'backend\resources\frontend\' -Recurse -Force"
   ```
4. 重启后端：
   ```bash
   cd backend
   python main.py
   ```
5. 清除浏览器缓存（Ctrl+Shift+Delete）
6. 重新访问 `http://localhost:8000`

### ✅ Logto 控制台配置

访问 https://logto.fary.chat 并检查前端应用 (ro4uk4fd2czd7cyx3wcbm):

- **Redirect URIs**: `http://localhost:8000/callback`
- **Post Logout URIs**: `http://localhost:8000`
- **CORS Origins**: `http://localhost:8000`
- **API Resources**: 关联 `http://localhost:8000`
