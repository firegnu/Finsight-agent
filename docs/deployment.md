# 部署指南

## 三种运行模式

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

### 3. Docker 模式（VPS / 任何支持 Docker 的环境推荐）

```bash
docker compose build      # 两阶段构建：node 构前端 → python 运行时
docker compose up -d      # 后台启动，:8000 暴露出来
```

一条命令起整个栈，相比方案 2 的额外优势：

- **依赖零污染**：Python 3.11 + node_modules 都在镜像里，VPS 只需要 Docker
- **首次启动自动初始化**：entrypoint 发现 `data/` 空了 → 自动 seed + 建 RAG 索引；已有则跳过
- **数据持久化**：宿主机 `./data` 目录挂进容器，镜像重 build 不丢 trace / approval / 向量库
- **健康检查**：内置 HEALTHCHECK，`docker compose ps` 直接看得到状态
- **日志统一**：`docker compose logs -f` 流式看

镜像大小约 571 MB。首次 build 3-5 分钟（取决于网络）。

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

## VPS 部署（从零到跑起来）

**适用场景**：演示给老板看 / 持续让团队访问 / 不希望本机一直开着。

**核心思路**：VPS 只装 Docker，其余全打进镜像，**一条命令跑起来**。

### 前置要求

- **VPS**：任何 Linux（Ubuntu 22.04 / Debian 12 最省心），**2 vCPU / 2 GB RAM / 20 GB 磁盘最低**（chromadb + onnxruntime 运行时约 500 MB 内存，首次 index 建议 1 GB+ 余量）
- **网络**：能访问 `open.bigmodel.cn`（Zhipu）+ `api.siliconflow.cn`（SiliconFlow）。**国内 VPS 最稳**，海外 VPS 可能抖动
- **端口**：至少开 22（SSH）+ 8000（应用）。用反代 + HTTPS 则再开 80/443

### 步骤 1 — 在 VPS 上装 Docker（首次）

```bash
# Debian/Ubuntu 一行装 Docker + compose 插件
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER        # 退出重连 SSH 生效
docker --version && docker compose version
```

### 步骤 2 — 把代码/镜像传上 VPS（二选一）

**路径 A：在 VPS 上 git clone + build**（要求 VPS 能访问 git 源）

```bash
git clone <repo-url> finsight-agent
cd finsight-agent
docker compose build                 # 在 VPS 上 build，~3-5 分钟
```

- ✅ 最简洁，后续更新 `git pull && docker compose build` 即可
- ⚠️ 踩过的坑：VPS 用代理/镜像源时，stage 2 的 `apt-get` 可能 503 失败（我们本地见过）。本项目 Dockerfile 已经避开 `apt`（HEALTHCHECK 用 python urllib），但如果以后加 apt 包要注意

**路径 B：本机 build → 导出镜像 → scp 到 VPS**（VPS 没 git / 网络慢）

```bash
# 本机
docker compose build
docker save finsight-agent:latest | gzip > finsight-agent.tar.gz
scp finsight-agent.tar.gz user@vps:/tmp/
scp docker-compose.yml user@vps:~/finsight-agent/
scp .env user@vps:~/finsight-agent/    # ⚠️ 见步骤 3

# VPS
cd ~/finsight-agent
gunzip -c /tmp/finsight-agent.tar.gz | docker load
# docker-compose.yml 里的 build 字段不影响 — image 已经存在，`up -d` 会直接用
```

- ✅ VPS 不需要 git，也不需要能上 GitHub
- ✅ 跳过 build，VPS 不吃 CPU
- ⚠️ 每次更新都得重复导入

### 步骤 3 — 配置 `.env`（含 API key）

`.env` **永远不要进 git**。两种方案：

1. **本机 scp 上去**（路径 B 已经做了）
2. **VPS 上手写**：`cp .env.example .env && vi .env`，填 `ZHIPU_API_KEY` + `LLM_EMBEDDING_API_KEY`

建议 `chmod 600 .env`，只有 owner 可读。

### 步骤 4 — 启动 + 首次初始化

```bash
docker compose up -d
docker compose logs -f                # 观察 entrypoint 自动 seed + index_cases
```

首次启动会看到：

```
[entrypoint] ./data/finsight.db missing — seeding mock data
[entrypoint] building RAG index (first run)
[entrypoint] launching: uvicorn ...
```

`index_cases.py` 会调 SiliconFlow 对 40+ 个 case 做 embedding，国内网络 10-30 秒搞定。完成后 uvicorn 起来。

### 步骤 5 — 冒烟验证

```bash
curl http://localhost:8000/api/health
# {"status":"ok","model":"glm-4.7-flash","provider":"zhipu",...}

docker compose ps
# STATUS 应该是 "Up X seconds (healthy)"
```

浏览器打开 `http://<vps-public-ip>:8000`，发一个查询，等 2-3 分钟（Zhipu 免费档就这速度，WaitingIndicator 会实时告诉你在哪一步）。

### 步骤 6（可选）—— 域名 + HTTPS

PoC 演示可以直接用 IP + 8000 跑起来，但：

- **浏览器 console 会 warn** 无 HTTPS（不影响功能）
- **SSE 长连接在某些公网环境**（运营商、学校网络）可能被掐

真要上 HTTPS，推荐 Caddy 一键自动签 Let's Encrypt：

```caddyfile
# /etc/caddy/Caddyfile
finsight.example.com {
    reverse_proxy 127.0.0.1:8000
    # Caddy 默认不 buffer，SSE 直接透传，零配置
}
```

或用 Nginx（注意 **一定要关 buffer**，见下面「SSE 反向代理注意事项」）。

### 更新流程

改了代码想重新部署：

**路径 A**：`git pull && docker compose build && docker compose up -d`
**路径 B**：本机重新 `docker save` → scp → `docker load` → `docker compose up -d`

**`./data/` 不会丢**，因为 volume 在宿主机上；镜像重 build 只换二进制。

### 备份建议

```bash
# VPS 上
tar czf finsight-data-$(date +%F).tar.gz data/
# scp 到别处或传云盘
```

`data/` 几百 MB 以内（SQLite + Chroma），压缩后更小。

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

**Q: Docker 和本地 dev 同时跑？**
A: 也会冲突（都要 :8000）。建议：UI 迭代走本地 dev（Vite HMR 秒级反馈），改完再 `docker compose build` 验证一次。

**Q: VPS 上 `docker compose up` 失败报 "LLM_EMBEDDING_API_KEY is required"？**
A: `.env` 没传或没填。entrypoint 在首次 index 时需要调 SiliconFlow，没 key 就 fail-fast。填好 key 后 `docker compose up -d` 重试。

**Q: Zhipu 调用在 VPS 上也这么慢？**
A: 是的，这是免费档固有延迟（10-45s / 轮，多轮累加 2-3 分钟）。非 bug。升级 Zhipu 付费档或换 provider 可缓解。前端 `WaitingIndicator` 已经实时显示等待秒数，避免用户以为卡死。

**Q: VPS 内存不够 `docker compose up` 被 OOM kill？**
A: 2 GB RAM 是最低要求；1 GB 起不来。首次 index_cases 瞬时内存需求最高（embedding 批处理 + onnxruntime），建议 2 GB+ 或临时加 swap。
