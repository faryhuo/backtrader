# routes 目录说明

- 作用：集中存放 FastAPI 路由模块，包括 `ai_routes.py`、`api_routes.py`、`live_routes.py`、`websocket_routes.py` 与静态挂载 `frontend_routes.py`。
- 责任边界：路由负责请求校验、参数转换与调用服务层/工具层，不直接承载业务核心或数据库操作。
- 命名与结构：新增路由文件命名为 `{feature}_routes.py`，对外暴露 `router`（或挂载函数），由 `src/service/app.py` 统一注册；请求/响应模型就近维护。
- 协作/测试：增加路由时更新接口文档/示例；至少进行导入与最小化接口冒烟（如启动 FastAPI 或调用 TestClient）以验证依赖与路径。
