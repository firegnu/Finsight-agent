# FinSight Agent — Session Handoff

**日期**：2026-04-18
**分支**：`main`（无未提交变更，远程已同步）
**最新 tag**：`v0.1.0-demo`
**最新 commit**：`80f8e09` test(rag): update RAG tests after method-* migration to skills

---

## 1. 会话摘要

完成了 Week 2 的 5 个核心功能日（Day 3.6 → Day 7），把项目从"跑通 MVP"升级到"接近生产可演示"形态：Agent 的工具从 3 个扩展到 6 个，新增了行业基准对标、实时 KPI 聚合、持久化的 HITL 审批、完整 Trace 审计、方法论 Skills 系统。剩下的只有**部署**和**UI 视觉升级**两个大项。

---

## 2. 完成的工作

### Day 3.6 — RAG UI 可视化
- `backend/knowledge_base/loader.py` + `/api/cases` + `/api/cases/{id}` 端点
- 前端 `CaseDetailModal`（react-markdown 渲染完整案例复盘）
- `ReasoningPanel` 对 `rag_search` tool_result 特殊渲染成可点击卡片
- `AnomalyCard` 的 references 从裸 ID 升级为可点击徽章（title 映射）
- Header 加"📚 N 个历史案例" 徽章

### Day 4 — financial_api + 实时 KPI 聚合
- 新表 `industry_benchmark`（8 条基准数据 + direction 字段）
- `backend/tools/financial_api.py` 工具 + 注册 registry
- `backend/db/kpi.py` SQLite 实时聚合（SUM + weighted avg），自动 alert 判断
- System prompt 引导 Agent 对每个 high/critical 异常调 financial_api 查基准
- AnomalyCard 自动显示"行业基准 vs 当前值"（Task 2.6 时预留的字段被激活）

### Day 5 — HITL 真实审批
- `approvals` 表（SQLite 持久化决策）
- `POST/GET/DELETE /api/approve/{report_id}` 三个端点
- 前端 `ApprovalButtons` 从纯本地 state 改为接真实 API，决策跨会话保留
- 支持 upsert（重新审批覆盖旧决策）+ 撤销
- 11 个 pytest 全覆盖（6 unit + 5 API）

### Day 6 — Trace 持久化 + 查看页
- `traces` + `trace_steps` 两张表
- Orchestrator 在每次 Agent 运行结束后把完整 TraceLog 写入 SQLite（含 final_report JSON）
- `GET /api/traces` 列表 + `GET /api/traces/{id}` 详情 + DELETE
- 前端 `TraceHistoryModal`：双栏 UI（左列表 + 右详情），含步骤展开、状态 chip、删除按钮
- Header 加"📋 历史分析"按钮打开 modal
- 10 个 pytest 全覆盖

### Day 7 — Skills 系统（集成进 Agent 运行时）
- **迁移 3 个方法论 markdown** 到 `backend/skills/`：
  - `anomaly-investigation.md`（逾期率四步调查）
  - `acquisition-diagnosis.md`（获客下滑四象限）
  - `churn-early-warning.md`（流失早期信号）
- **新加 2 个 skills**：
  - `cross-region-comparison.md`（跨区域对比三层次）
  - `executive-briefing.md`（主管汇报 BLUF 格式）
- RAG 案例库瘦身为 2 个**真实事件复盘**（east-2024-q3 + south-2023），职责清晰分离
- `backend/skills/loader.py` 读 markdown + frontmatter
- `backend/tools/use_skill.py` 新工具（第 6 个），参数用 enum 限制在当前可用 skills
- `backend/agent/prompts.py` 动态构建 `_SKILLS_CATALOG` 注入 SYSTEM_PROMPT
- 前端 `SkillDetailModal` + ReasoningPanel 对 `use_skill` 渲染琥珀色卡片 + Header "🎯 5 个 skills" 徽章
- `GET /api/skills` + `GET /api/skills/{name}` 端点
- 11 个 pytest 全覆盖
- **端到端验证**：用户问 "给领导做个汇报" → Agent 自主调 `use_skill('executive-briefing')` ✓

### 文档 / 品牌清理
- 去除代码库所有"面试"/"Essex"/"EARS"/"Anomalix"/"TaskTrac" 字样（3 个文档 20+ 处）
- 重建 `v0.1.0-demo` tag（清理 tag message）

---

## 3. 待完成的工作

### 部署（用户明确放最后，~8-9h）
- **Day 8 FastAPI 托管前端静态文件**（单进程部署方案）
  - `main.py` 加 `StaticFiles` 挂载 `frontend/dist`
  - 生产 build + README 加部署步骤
- **Day 9 VPS 部署 + OpenRouter 接入**
  - 云 VPS（用户已决定不用 Windows 4060Ti，改云 + OpenRouter 免费模型）
  - 需要处理 embedding：OpenRouter 不做 embedding，需要本地 sentence-transformers（bge-small-zh，~200MB）或阿里云 embedding
  - 多 Provider UI 切换（顶栏下拉）

### UI 视觉升级（用户主导，用 Claude Design）
- 当前 UI 是裸 Tailwind，可演示但朴素
- 用户会自己做

### 潜在优化（Nice-to-have）
- 处理"你好"/闲聊类问题时，ReportPanel 的空状态文案（当前"等待分析结果"不贴切）
- System prompt 加一段"无关问题礼貌重定向"的指引

---

## 4. 关键决策

### 部署策略大转向
原计划 Windows 4060Ti + Ollama + 公网 IP；用户改为**云 VPS + OpenRouter 免费模型 + 轻量 embedding**。理由：VPS 永远在线、不依赖用户家里机器、零 API 费用（OpenRouter 有免费模型）、更"生产化"。

### Provider-Agnostic 设计坚持到底
每次遇到"给 LM Studio 特化"的诱惑都拒绝（`extra_body`、`response_format`），保持 OpenAI SDK 兼容层纯净。归一化层（`reasoning_content` 合并到 `content`）对所有 provider 透明工作。

### Skills vs RAG 职责分离
**关键架构决策**：
- **RAG 案例库** = 真实历史事件复盘（向量相似度被动检索）
- **Skills 库** = 结构化方法论 SOP（按名字显式加载）
- 迁移了 3 个 method-*.md 从 RAG 到 Skills，避免功能重合

### 参考 Anthropic 官方设计
Skills 的 SKILL.md 格式（YAML frontmatter + markdown）严格参照 `anthropics/financial-services-plugins`。官方 plugin 聚焦投行建模（DCF/LBO），我们聚焦零售银行运营监控，做领域适配。

### financial_api 是 SQLite 模拟
诚实的 trade-off：`financial_api` 查的是本地 `industry_benchmark` 表而非真实 Alpha Vantage/Bloomberg，工具 schema 完全一致，替换只需改实现。面试叙事："外部数据源抽象层"。

### 架构层面"两个数据源 × 两个抽象层"
```
本司数据 (SQLite credit_card_metrics) ← sql_query / anomaly_detect / KPI 聚合
行业基准 (SQLite industry_benchmark)  ← financial_api
历史事件 (Chroma RAG)                ← rag_search
方法论 SOP (backend/skills/)         ← use_skill
LLM 层 (OpenAI 兼容接口 + 归一化)     ← chat / embed
报告层 (Pydantic schema)             ← report_gen
审计层 (traces + approvals)          ← 全程持久化
```

---

## 5. 重要文件

### 后端核心
- `backend/main.py` — FastAPI 入口，12 个 REST 端点
- `backend/agent/orchestrator.py` — ReAct 循环 + SSE + Trace 持久化
- `backend/agent/prompts.py` — 动态 SYSTEM_PROMPT（注入 skills catalog）
- `backend/agent/models.py` — Pydantic 模型
- `backend/tools/registry.py` — 6 工具注册表
- `backend/tools/{use_skill,sql_query,anomaly_detect,financial_api,rag_search,report_gen}.py`
- `backend/llm/client.py` — Provider-agnostic + reasoning_content 归一化 + embed()
- `backend/db/{database,kpi,approvals,traces}.py` — 数据访问层
- `backend/skills/loader.py` + `backend/skills/*.md`（5 个 SKILL.md）
- `backend/knowledge_base/loader.py` + `backend/knowledge_base/cases/*.md`（2 个真实案例）

### 前端核心
- `frontend/src/App.tsx` — 顶层布局 + 3 个 modal 管理
- `frontend/src/components/`：
  - `Header.tsx`（含 skills/cases 徽章 + 历史分析按钮）
  - `ReasoningPanel.tsx`（对 use_skill/rag_search 特殊渲染）
  - `ReportPanel.tsx`（含 ApprovalButtons 集成）
  - `AnomalyCard.tsx`（显示 baseline_value + references 可点击徽章）
  - `ActionItemCard.tsx`
  - `ApprovalButtons.tsx`（真实 API 驱动）
  - `CaseDetailModal.tsx` / `SkillDetailModal.tsx` / `TraceHistoryModal.tsx`
  - `ChatInput.tsx` / `KPICards.tsx`
- `frontend/src/hooks/`：`useSSE.ts` / `useCases.ts` / `useSkills.ts`
- `frontend/src/types/index.ts` — 全部 TS 类型（镜像 Pydantic）

### 脚本 / 数据
- `scripts/seed_data.py` — SQLite schema + 种子数据（含 approvals/traces 空表）
- `scripts/index_cases.py` — Chroma 向量索引（RAG 重建）
- `data/finsight.db` — SQLite（gitignore）
- `data/chroma/` — Chroma 持久化（gitignore）

### 配置
- `.env.example` + `.env`（provider 切换的 3 段式配置）
- `Makefile` — 常用命令
- `backend/config.py` — Pydantic Settings

### 文档
- `FinSight Agent.md` — 原始设计文档
- `docs/plans/2026-04-18-finsight-agent-mvp.md` — 完整实施计划（已更新多次）
- `README.md` — 启动指南 + 架构 + FAQ
- 本文件 `HANDOFF.md`

---

## 6. 下一步建议（按优先级）

### P0 — 首要任务
**如果要继续推进**：Day 8 FastAPI 托管前端静态文件（2h）
- 加 `StaticFiles` 挂载 `frontend/dist`
- 开发/生产双模式区分
- 产出 `docs/deployment.md`

**如果要先休息一下**：项目已经 demo-ready，可以先**录屏 2-3 分钟**做展示物料。本地 `make dev-backend` + `make dev-frontend` 随时可以演示。

### P1 — 次要任务
**Day 9 VPS 部署 + OpenRouter**（4h）
- 选 VPS（阿里云 2 核 4G 足够）
- 接 OpenRouter（`LLM_BASE_URL=https://openrouter.ai/api/v1`，免费模型如 `meta-llama/llama-3.1-8b-instruct:free`）
- Embedding 方案决定：
  - **方案 A**: 容器内跑 sentence-transformers + bge-small-zh（~300MB 镜像增量）
  - **方案 B**: 用阿里通义免费 embedding API
  - **推荐 A**：完全自包含，无第三方 embedding key 依赖
- 多 Provider UI 切换器（可选，可合并到这一天）

### P2 — 可选优化
1. **空对话体验**：ReportPanel 的 status=done + report=null 时显示"此次为对话式回复，未生成结构化报告"（当前显示"等待分析结果"有歧义）
2. **System prompt 加无关问题引导**：让 Agent 明确拒绝 off-topic，引导用户问业务问题
3. **历史问题重跑**：TraceHistoryModal 加"基于此 trace 再问一次"按钮
4. **report_id → trace_id 反向导航**：在 ReportPanel 加"查看完整 trace"链接

### UI 视觉升级（用户主导）
用户说要用 Claude Design 做，我这边不动。

---

## 7. 当前质量指标

- ✅ **pytest 68/68 pass**（anomaly_detect 7 + approvals 11 + financial_api 4 + kpi 4 + rag_search 5 + seed 5 + skills 11 + sql_validator 11 + traces 10）
- ✅ 前端 TypeScript 0 error（`npm run build` 通过）
- ✅ 前端生产 build: **343 kB JS / 19.6 kB CSS**（gzip 104 / 4.5 kB）
- ✅ 端到端完整分析耗时 **~100-130s**（本地 LM Studio + GLM-4.7-Flash）
- ✅ 6 个 Agent 工具全部集成 + 自主调度验证通过
- ✅ Git 工作区干净，远程同步（main + v0.1.0-demo tag）

---

## 8. 启动命令速查

```bash
# 安装
make install
make seed

# 开发（两个终端）
make dev-backend    # FastAPI @ :8000
make dev-frontend   # Vite @ :5173

# 测试
make test           # 68 个 pytest 用例

# 构建
make build          # 前端生产 build
```

**前置条件**：LM Studio 需加载 `zai-org/glm-4.7-flash` + `text-embedding-nomic-embed-text-v1.5` 两个模型。如果切 OpenRouter/DeepSeek/通义，改 `.env` 三个变量即可。
