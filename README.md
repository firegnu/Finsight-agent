# FinSight Agent

金融数据智能分析 Agent（MVP 演示项目）——用户用自然语言提问，Agent 自动从多数据源采集数据、检测异常、生成带有优先级的行动建议报告。核心理念：**从数据到洞察到行动**。

## 技术栈

- **后端**: Python 3.11 + FastAPI + OpenAI SDK + Pydantic v2 + SQLite + ChromaDB + NumPy
- **前端**: React 19 + TypeScript + Vite 8 + Tailwind CSS v3
- **LLM（provider-agnostic）**: DeepSeek V3（默认、付费但极便宜、速度快）/ 智谱云 GLM-4.7-Flash（免费档、慢）/ 本地 LM Studio，前端下拉实时切换；所有 OpenAI 兼容 provider 改 `.env` 即可加入
- **Embedding**: SiliconFlow `BAAI/bge-m3`（默认、免费、1024 维），单 provider 锁死
- **架构**: ReAct 循环 + SSE 流式推送 + 6 个工具（sql_query / anomaly_detect / financial_api / rag_search / use_skill / report_gen）+ HITL 审批 + trace 持久化

## 快速启动

### 前置条件

- Python 3.11+（推荐 conda env）
- Node.js 20+
- 至少一个 LLM API key，默认配置需要：
  - **DeepSeek**（聊天）：从 [platform.deepseek.com](https://platform.deepseek.com) 申请，新用户送 ~10 元额度，单次完整分析 ≈ ¥0.03-0.05
  - **SiliconFlow**（embedding）：从 [siliconflow.cn](https://siliconflow.cn) 免费申请，`BAAI/bge-m3` 免费
  - 或**智谱云**免费档替代聊天（慢但永久免费）：从 [bigmodel.cn](https://open.bigmodel.cn) 申请 `glm-4.7-flash`
- **或**用本地 LM Studio（同时加载 chat 模型 + embedding 模型）避开外部 API——改 `.env` 即可

### 一键启动（Makefile）

```bash
make install        # 安装前后端依赖
cp .env.example .env && $EDITOR .env   # 填入 DEEPSEEK_API_KEY + LLM_EMBEDDING_API_KEY
make seed           # 生成 SQLite 业务数据
python scripts/index_cases.py          # 构建 Chroma 向量索引

# 分别在两个终端跑：
make dev-backend    # FastAPI @ :8000（含 --reload 热重启）
make dev-frontend   # Vite    @ :5173（含 HMR 热更新）
```

打开 http://localhost:5173 即可。

### 生产预览（单进程模式）

```bash
make serve-prod     # build 前端 + uvicorn（无 reload），:8000 同时服务 API + 静态
```

打开 http://localhost:8000——和 VPS 部署后的形态完全一致。详见 [docs/deployment.md](docs/deployment.md)。

### 验证

```bash
curl http://localhost:8000/api/health
# {"status":"ok","model":"deepseek-chat","provider":"deepseek","default_provider_id":"deepseek"}

curl http://localhost:8000/api/providers
# 返回所有已配置的 chat provider 列表（embedding 不会出现在这里）

curl -N -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"信用卡业务上个月有什么异常？","provider_id":"deepseek"}'
```

### 跑测试

```bash
make test
# 80 passed in ~4s
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

### 预置三个 provider

`.env` 默认包含 `deepseek`（DeepSeek V3 付费但极便宜，速度快、工具调用强，**默认**）+ `zhipu`（智谱云 GLM-4.7-Flash 免费，但并发=1 比较慢）+ `lmstudio`（本地 LM Studio）：

```bash
DEFAULT_PROVIDER_ID=deepseek

LMSTUDIO_LABEL=本地 LM Studio (GLM-4.7-Flash)
LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
LMSTUDIO_API_KEY=lm-studio
LMSTUDIO_MODEL=zai-org/glm-4.7-flash

ZHIPU_LABEL=智谱云 GLM-4.7-Flash
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
ZHIPU_API_KEY=<在 bigmodel.cn 控制台申请，免费>
ZHIPU_MODEL=glm-4.7-flash

DEEPSEEK_LABEL=DeepSeek V3
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=<在 platform.deepseek.com 申请，新用户送 ~10 元>
DEEPSEEK_MODEL=deepseek-chat
```

### 新增一个 provider（如通义千问 / Moonshot / OpenAI）

1. `.env` 里加 4 行：`XXX_LABEL` / `XXX_BASE_URL` / `XXX_API_KEY` / `XXX_MODEL`
2. `backend/config.py` 的 `PROVIDER_IDS` 元组里追加 `"xxx"`
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
| Skills 和 RAG 的区别？ | RAG = 真实历史事件复盘（向量相似度被动检索）；Skills = 结构化方法论 SOP（`use_skill` 按名字显式加载）。两种召回机制故意分开，避免功能重合 |
| Provider 切换？ | 多 provider 预置在 `.env`（`{ID}_LABEL/_BASE_URL/_API_KEY/_MODEL`），前端 Header 下拉实时切换，选择持久化到 `localStorage`。每次 `/api/analyze` 带 `provider_id`，trace 记录每次用的是哪个。Embedding 单独锁死 |
| Off-topic 问题怎么处理？ | System prompt 明确指引：闲聊/非业务问题不调用任何工具，直接 final_text 礼貌重定向。ReportPanel 在 `status=done` 且无 report 时显示"对话式回复"文案 |
| SSE vs WebSocket？ | 单向推送够用，SSE 简单、天然兼容 HTTP/2、在 Nginx 反向代理里配置只要 `proxy_buffering off` |
| 部署方案？ | 单进程方案：FastAPI 同端口服务 API + `frontend/dist/` 静态文件（同源无 CORS）；`make serve-prod` 本地预览，未来 Docker 化部署到 VPS |
| 生产扩展？ | SQLite → PostgreSQL，Chroma 已在用，Redis 可加做 trace 缓存，Docker Compose 一键部署 |

## 项目文档

- `FinSight Agent.md` — 原始设计文档
- `HANDOFF.md` — 会话交接摘要（当前进度、关键决策、下一步）
- `docs/deployment.md` — 本地生产预览 + VPS 部署指南
- `docs/plans/2026-04-18-finsight-agent-mvp.md` — 历史实施计划

## 开发路线

- **Week 1 ✅**: 后端 ReAct 循环 + 3 工具 + SSE + React 前端，端到端可演示
- **Week 2 ✅**:
  - RAG 历史案例库（Chroma + 2 个真实历史事件复盘 + `rag_search` 工具）
  - `financial_api` 工具 + 行业基准表
  - KPI 卡片接真实 SQLite 聚合
  - HITL 真实审批（`POST /api/approve` + SQLite 持久化）
  - Trace 日志持久化 + 历史分析 modal（含"再问一次"回放）
  - Skills 系统（5 个 SKILL.md 方法论 + `use_skill` 工具 + 动态 catalog 注入 system prompt）
  - **多 Provider 切换器**：三 provider 预置（本地 LM Studio + 智谱云 + DeepSeek），前端 Header 下拉运行时切换，选择 localStorage 持久化，每个 trace 记录 `provider_id`
  - **SiliconFlow bge-m3 embedding**：云端免费 1024 维，Chroma 索引与 embedding 模型强绑定（换模型需 `python scripts/index_cases.py` 重建）
- **Day 8 ✅**: FastAPI 托管前端静态文件（单进程部署）—— `make serve-prod` 同端口服务 API + SPA
- **Day 9（计划中）**: Docker + VPS 部署
- **UI 视觉升级（用户主导）**: 用 Claude Design 重做

## 目录结构

```
Finsight-Agent/
├── backend/                    # FastAPI 后端
│   ├── agent/                 # orchestrator / prompts / Pydantic models
│   ├── tools/                 # sql_query / anomaly_detect / financial_api / rag_search / use_skill / report_gen + registry
│   ├── llm/                   # OpenAI 兼容 client（provider 工厂 + reasoning_content 归一化 + 独立 embedding client）
│   ├── db/                    # SQLite 连接 + kpi 聚合 + approvals + traces 持久化
│   ├── sse/                   # SSE 事件序列化
│   ├── skills/                # 方法论 skill 库（5 个 SKILL.md + loader）
│   ├── knowledge_base/        # RAG 案例库（真实历史事件复盘 + loader）
│   └── tests/                 # pytest (80 个用例)
├── frontend/                   # React + Vite + TS
│   └── src/
│       ├── components/        # Header / KPI / ChatInput / Reasoning / Report /
│       │                      # AnomalyCard / ActionItemCard / ApprovalButtons /
│       │                      # CaseDetailModal / SkillDetailModal / TraceHistoryModal /
│       │                      # ProviderSwitcher
│       ├── hooks/             # useSSE / useCases / useSkills / useProviders
│       ├── types/             # 与 Pydantic 对齐的 TS 类型
│       └── utils/             # fetchKPI / fetchHealth / fetchProviders / ...
├── scripts/
│   ├── seed_data.py           # 生成业务数据 + 行业基准（随机 seed=42，可重复）
│   └── index_cases.py         # 构建 Chroma 向量索引（idempotent；自动清理孤立 UUID 目录）
├── data/                       # SQLite DB + Chroma（gitignore，含备份子目录）
├── docs/
│   ├── deployment.md          # 本地生产预览 + VPS 部署指南
│   └── plans/                 # 历史实施计划
└── Makefile                    # install / seed / dev-{backend,frontend} / test / build / serve-prod / clean
```
