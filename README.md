# FinSight Agent

金融数据智能分析 Agent（MVP 演示项目）——用户用自然语言提问，Agent 自动从多数据源采集数据、检测异常、生成带有优先级的行动建议报告。核心理念：**从数据到洞察到行动**。

## 技术栈

- **后端**: Python 3.11 + FastAPI + OpenAI SDK + Pydantic v2 + SQLite + NumPy
- **前端**: React 19 + TypeScript + Vite 8 + Tailwind CSS v3
- **LLM（provider-agnostic）**: 本地 LM Studio / DeepSeek / 通义千问 / OpenAI，改 `.env` 切换，零代码改动
- **架构**: ReAct 循环 + SSE 流式推送 + 3 个工具（sql_query / anomaly_detect / report_gen）

## 快速启动

### 前置条件

- Python 3.11+（推荐 conda env）
- Node.js 20+
- 一个 OpenAI 兼容的 LLM 后端，任选其一：
  - **LM Studio（本地推荐）**：加载 `zai-org/glm-4.7-flash`（或其他非 thinking chat 模型），启动 server 监听 `localhost:1234`
  - **DeepSeek API**：准备 API key，`.env` 改成 `https://api.deepseek.com/v1` + `deepseek-chat`
  - **通义千问 / OpenAI**：同理改 `.env`

### 一键启动（Makefile）

```bash
make install        # 安装前后端依赖
make seed           # 生成模拟数据

# 分别在两个终端跑：
make dev-backend    # FastAPI @ :8000
make dev-frontend   # Vite   @ :5173
```

打开 http://localhost:5173 即可。

### 手动启动

```bash
# 后端
conda create -n finsight python=3.11 -y && conda activate finsight
pip install -r backend/requirements.txt
cp .env.example .env                          # 首次
python scripts/seed_data.py                   # 生成 data/finsight.db
uvicorn backend.main:app --reload --port 8000

# 前端
cd frontend && npm install && npm run dev
```

### 验证

```bash
curl http://localhost:8000/api/health
# {"status":"ok","model":"zai-org/glm-4.7-flash","provider":"lmstudio"}

curl -N -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"信用卡业务上个月有什么异常？"}'
```

### 跑测试

```bash
make test
# 23 passed in ~0.3s
```

## 演示场景

**埋入的异常**（由 `scripts/seed_data.py` 注入）：

| 异常 | 区域 | 期间 | 数值 | 严重度 |
|---|---|---|---|---|
| 逾期率飙升 | 华东 | 2026-03 | 5.8%（历史均值 ~3.2%） | ≈13σ critical |
| 获客量断崖 | 华南 | 2026-02 | 1800（均值 ~2600） | ≈-5σ high |
| 获客量断崖 | 华南 | 2026-03 | 1450 | ≈-7σ critical |
| 激活率同步下滑 | 华南 | 2026-02/03 | -4~6pp | 中 |
| 催收回收率 / 投诉量 | 华东 | 2026-03 | 催收 -5pp，投诉 +40% | 伴生指标 |

**推荐演示问题**：
1. "信用卡业务上个月有什么异常？"（主干演示，展示全部工具链）
2. "华东区逾期率为什么上升了？"（聚焦根因推理）
3. "对比各区域 2026-03 的获客量"（纯数据查询，无异常分析）

## 切换 LLM Provider

本项目支持**多 provider 并存 + 前端运行时切换**。`.env` 里同时配置多个 provider，启动后前端 Header 右上角的下拉菜单可实时切换，选择持久化到 `localStorage`，每次 `/api/analyze` 请求会带上 `provider_id`。Embedding 单独配置且锁死（见下文）。

### 预置两个 provider

`.env` 默认包含 `lmstudio`（本地 LM Studio）+ `zhipu`（智谱云 GLM-4.7-Flash 免费）两个：

```bash
DEFAULT_PROVIDER_ID=zhipu

LMSTUDIO_LABEL=本地 LM Studio (GLM-4.7-Flash)
LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
LMSTUDIO_API_KEY=lm-studio
LMSTUDIO_MODEL=zai-org/glm-4.7-flash

ZHIPU_LABEL=智谱云 GLM-4.7-Flash
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
ZHIPU_API_KEY=<在 bigmodel.cn 控制台申请，免费>
ZHIPU_MODEL=glm-4.7-flash
```

### 新增一个 provider（如 DeepSeek / 通义千问 / OpenAI）

1. `.env` 里加 4 行：`DEEPSEEK_LABEL` / `DEEPSEEK_BASE_URL` / `DEEPSEEK_API_KEY` / `DEEPSEEK_MODEL`
2. `backend/config.py` 的 `PROVIDER_IDS` 元组里追加 `"deepseek"`
3. 重启后端。前端下拉会自动出现新选项

常见 provider 参考：

| Provider | base_url | 模型示例 |
|---|---|---|
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | `glm-4.7-flash`（免费）|
| DashScope | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| OpenRouter | `https://openrouter.ai/api/v1` | `anthropic/claude-haiku-4.5` |

`llm/client.py` 里有响应归一化层，自动把 `reasoning_content`（DeepSeek R1 / OpenAI o1 / Qwen thinking 这类 reasoning 模型的思考字段）合并到 `content`，所以换模型不用改业务代码。

### 为什么一个 `base_url` 就能覆盖大部分 provider？

市面上 LLM API 其实只有三大标准：**OpenAI API**、**Anthropic Messages API**、**Google Gemini API**，三者结构互不兼容。但 OpenAI 格式是事实上的通用标准——绝大多数 provider 都原生支持它：

- **国内全员**：DeepSeek、Qwen/DashScope、智谱 GLM、Moonshot Kimi、MiniMax、百川、零一万物
- **国外非三巨头**：Groq、Mistral、Together AI、Fireworks、Perplexity、xAI Grok
- **自托管**：Ollama、LM Studio、vLLM、llama.cpp server
- **聚合器**：OpenRouter（一个 key 转发到 100+ 模型）
- **三巨头的兼容层**：OpenAI 原生；Anthropic 和 Gemini 也各自提供了 OpenAI 兼容端点（功能阉割版，不支持 prompt caching / thinking / grounding 这些独门能力）

所以这个架构 **≈95% 的 provider 直接换 `.env` 就能用**。唯一需要写独立 adapter 的场景是想用 Anthropic / Gemini 的原生高级能力（prompt caching、extended thinking、grounding），或 Cohere / Bedrock 这类非主流接口——目前项目没这个需求。

### 多 provider 的一个硬约束：chat 可以切，embedding 必须锁死

chat LLM 是无状态调用，切换 provider 零代价。但 **embedding 不一样**——向量空间和具体的 embedding 模型强绑定：

- 不同 embedding 模型输出的向量坐标系完全不同，即使维度相同也不兼容
- 查询向量和库里已存向量必须来自**同一个模型**，否则检索结果退化成随机
- 换 embedding provider = 必须重建整个 Chroma 向量库（`python scripts/index_cases.py`）

所以 `.env` 里**chat** 用 `{PROVIDER_ID}_*` 格式（可多组）允许前端 UI 切换，**embedding** 固定用一组 `LLM_EMBEDDING_*` 变量，对用户透明，不出现在 UI 切换器里。建库之后想换 embedding 模型，必须跑 `python scripts/index_cases.py` 重建 Chroma。

## 架构要点（常见追问 FAQ）

| 追问 | 回答 |
|---|---|
| Text-to-SQL 准确率怎么保证？ | 硬编码字段元数据到 prompt + 3 个 few-shot + SQL 校验器（SELECT 白名单）+ 执行失败自动重试 2 次 |
| 为什么不用 LangChain？ | Outer/Inner Harness 自研，控制力和可审计性强，金融场景需要每步 trace；LangChain 抽象过深，调试成本高 |
| 异常检测方法？ | 统计：历史均值 ± 标准差，deviation 倍数映射到 4 级 severity。不过度工程化，不引入 ML 模型 |
| 怎么防止 LLM 编造数据？ | Prompt 硬约束"数字必须来自工具返回" + Pydantic 输出 schema 校验 + SQL 只读白名单 |
| Provider 切换？ | 多 provider 预置在 `.env`，前端 Header 下拉实时切换，选择持久化到 `localStorage`。每次 `/api/analyze` 带 `provider_id`，trace 记录每次用的是哪个。Embedding 单独锁死 |
| SSE vs WebSocket？ | 单向推送够用，SSE 简单、天然兼容 HTTP/2、在 Nginx 反向代理里配置只要 `proxy_buffering off` |
| 生产扩展？ | SQLite → PostgreSQL，增加 Chroma 做 RAG 案例检索，Redis 做 Trace 日志缓存，Docker Compose 一键部署 |

## 项目文档

- `FinSight Agent.md` — 原始设计文档
- `docs/plans/2026-04-18-finsight-agent-mvp.md` — 两天 MVP 实施计划 + 下周占位清单

## 开发路线

- **Week 1（当前）**: 后端 ReAct 循环 + 3 工具 + SSE + React 前端，端到端可演示
- **Week 2（占位预留）**:
  - RAG 历史案例库（Chroma + 3-5 案例 markdown + `rag_search` 工具）
  - `financial_api` 工具 + 行业基准表
  - 多 Provider UI 切换器
  - Human-in-the-Loop 真实审批（POST `/api/approve`）
  - Trace 日志持久化 + 查看页
  - KPI 卡片接真实 SQLite 聚合
  - Docker Compose + VPS 部署
  - UI 用 Claude Design 重做视觉
  - Claude Code Skills（`.claude/skills/`）——参考 Anthropic 官方 `financial-services-plugins` 格式，为零售银行运营场景做领域适配

## 目录结构

```
Finsight-agent/
├── backend/                    # FastAPI 后端
│   ├── agent/                 # ReAct orchestrator + prompts + Pydantic models
│   ├── tools/                 # sql_query / anomaly_detect / report_gen + registry
│   ├── llm/                   # OpenAI 兼容 client + reasoning_content 归一化
│   ├── db/                    # SQLite 连接
│   ├── sse/                   # SSE 事件序列化
│   └── tests/                 # pytest (23 个用例)
├── frontend/                   # React + Vite + TS
│   └── src/
│       ├── components/        # Header / KPI / ChatInput / Reasoning / Report / Cards
│       ├── hooks/             # useSSE.ts
│       ├── types/             # 与 Pydantic 对齐的 TS 类型
│       └── utils/             # fetchKPI / fetchHealth
├── scripts/
│   └── seed_data.py           # 生成 60 行模拟数据（random seed=42 可重复）
├── data/                       # SQLite DB（gitignore）
├── docs/plans/                # 实施计划
└── Makefile                    # 常用命令快捷方式
```
