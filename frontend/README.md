# 电商问数前端（Vue 3）

基于 Vue 3 + Vite + TypeScript 的问数工作台，对接本项目 FastAPI 后端的 SSE 问数接口和会话管理接口。

## 功能

- 自然语言问数，SSE 实时展示 LangGraph 执行过程
- 查询结果表格、复制 JSON、下载 CSV
- Redis 短期会话：刷新页面后可从侧边栏恢复最近会话
- Qdrant 长期记忆：查看当前会话写入的向量记忆
- 多轮追问：自动携带 `session_id`，由后端完成指代改写
- 移动端抽屉式侧边栏，桌面端双栏布局

## 本地运行

```bash
cd frontend
npm install
npm run dev
```

默认地址：`http://127.0.0.1:5173`

开发服务器会把 `/api` 代理到 `http://127.0.0.1:8000`。如需修改后端地址，复制 `.env.example` 为 `.env` 并调整 `VITE_DEV_PROXY_TARGET`。

## 构建

```bash
npm run build
npm run preview
```

生产部署时，需要由 Nginx 等静态服务器把 `/api` 反向代理到 FastAPI；
也可以设置 `VITE_API_BASE_URL=https://your-backend.example.com` 后重新构建。

> 当前会话默认使用 `user_id=default`。如需按用户隔离长期记忆，可修改
> `src/composables/useChat.ts` 中的 `USER_ID`，或接入登录态后动态传入。

## 后端接口

- `POST /api/query`：SSE 问数流，事件类型包括 `session`、`progress`、`result`、`error`
- `GET /api/sessions?user_id=default`：会话列表
- `GET /api/sessions/{session_id}`：会话详情
- `DELETE /api/sessions/{session_id}`：删除会话及其长期记忆
- `GET /api/sessions/{session_id}/memories`：查看会话长期记忆
