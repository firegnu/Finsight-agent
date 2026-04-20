# 部署指南

## 两种运行模式

### 1. 开发模式（前后端分离，推荐日常开发用）

两个终端分别跑：

```bash
make dev-backend      # FastAPI @ :8000，--reload 自动重启
make dev-frontend     # Vite @ :5173，HMR 热更新
```

浏览器访问 **http://localhost:5173**。Vite 会把 `/api/*` 请求代理到 `:8000`。

### 2. 生产模式（单进程，用于部署预览 + VPS）

```bash
make serve-prod       # = make build + uvicorn（无 reload）
```

浏览器访问 **http://localhost:8000**。FastAPI 一个进程同时提供：
- `/api/*` → REST + SSE
- 其他路径 → `frontend/dist/` 里的静态文件（SPA fallback 到 `index.html`）

没有 CORS，没有独立前端服务，干净的单端口部署。

---

## 生产模式工作原理

`backend/main.py` 末尾有一段检测逻辑：

```python
_DIST_DIR = <repo>/frontend/dist

if _DIST_DIR.is_dir() and (_DIST_DIR / "index.html").is_file():
    # 注册 SPA catch-all：非 /api/* 的路径
    #   - 真实文件存在 → FileResponse
    #   - 否则 → index.html（SPA 深链不 404）
```

**关键特性**：
- `dist/` 不存在时**优雅降级**成 API-only 模式，开发模式照常工作
- `/api/*` 路由优先匹配，catch-all 不会吞掉 API 404
- 根路径 `/` 自动回退到 `index.html`
- 资源路径 `/assets/*.js` / `/favicon.svg` 直接返回真文件

---

## 首次生产启动 checklist

```bash
# 1. 安装依赖（首次）
make install

# 2. 生成模拟数据（首次；data/finsight.db 不在 git 里）
make seed

# 3. 构建向量索引（首次；data/chroma/ 不在 git 里）
python scripts/index_cases.py

# 4. 配置 .env（首次；至少设 ZHIPU_API_KEY + LLM_EMBEDDING_API_KEY）
cp .env.example .env
$EDITOR .env

# 5. 启动
make serve-prod
```

访问 http://localhost:8000 确认应用正常。

---

## 环境变量要点

| 变量 | 开发模式 | 生产模式 |
|---|---|---|
| `DEFAULT_PROVIDER_ID` | `zhipu` 或 `lmstudio` | 建议 `zhipu` (VPS 无本地模型) |
| `CORS_ORIGINS` | 留默认 | 单进程部署**无关紧要**（同源），但 Docker/多域名需要改 |
| `ZHIPU_API_KEY` | 可选 | **必填**（或删掉这个 provider） |
| `LLM_EMBEDDING_API_KEY` | 可选（本地 LM Studio 用占位符）| **必填**（SiliconFlow key）|

**关键**：`.env` 是 gitignored 的，API key 永远不会进 git。部署时通过环境变量或 secret 挂载传入。

---

## 数据持久化

单进程模式下，两类数据写入本地磁盘：

| 目录/文件 | 内容 | 部署时处理 |
|---|---|---|
| `data/finsight.db` | SQLite（业务数据 + traces + approvals）| Docker 用 volume 挂载 |
| `data/chroma/` | 向量库（bge-m3 1024 维）| Docker 用 volume 挂载，或容器内重建 |

两者都**必须持久化**到容器外，否则每次重启丢失 trace 历史 + 审批记录。

---

## SSE 反向代理注意事项

如果前面加 Nginx / Caddy 做 HTTPS 终结，**必须禁用缓冲**否则 SSE 流会被卡住：

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_buffering off;          # ← 关键：SSE 必需
    proxy_cache off;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
}
```

如果直接暴露 uvicorn（不经 Nginx），此配置无关。

---

## 常见问题

**Q: 生产模式下改了前端代码，为什么不生效？**
A: 生产模式吃的是 `frontend/dist/` 的构建产物，不是源码。改完跑 `make build` 或直接 `make serve-prod`（会先 build）。

**Q: 我只改了后端，需要 rebuild 前端吗？**
A: 不需要。直接重启 uvicorn 即可，前端 dist/ 不变。

**Q: 同时跑 dev-backend 和 serve-prod 会冲突吗？**
A: 会，两者都监听 `:8000`。选一种模式跑。
