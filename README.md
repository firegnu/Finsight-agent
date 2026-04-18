# FinSight Agent

金融数据智能分析 Agent（面试演示项目）——用户用自然语言提问，Agent 自动从多数据源采集数据、检测异常、生成带有优先级的行动建议报告。对标 Essex EARS 平台（Ask EARS + Anomalix + TaskTrac）。

## 技术栈

- **后端**: Python 3.11 + FastAPI + OpenAI SDK + Pydantic v2 + SQLite + NumPy
- **前端**: React 18 + TypeScript + Vite + Tailwind CSS（Day 2 实装）
- **LLM**: 本地 LM Studio (Qwen3.5-35B-A3B) → 下周扩展 DeepSeek/Qwen 在线 API
- **架构**: ReAct 循环 + SSE 流式推送 + 3 个工具（sql_query / anomaly_detect / report_gen）

## 快速启动

### 前置条件

- Python 3.11+（推荐 conda env）
- Node.js 20+（Day 2 前端）
- LM Studio：下载 `qwen3.5-35b-a3b` 并加载到内存，启动 server 监听 `localhost:1234`

### 后端

```bash
# 1. 创建 conda env
conda create -n finsight python=3.11 -y
conda activate finsight

# 2. 安装依赖
pip install -r backend/requirements.txt

# 3. 配置环境变量
cp .env.example .env      # 默认指向 localhost:1234

# 4. 生成模拟数据（60 行，含埋入的异常点）
python scripts/seed_data.py

# 5. 启动 API 服务器
uvicorn backend.main:app --reload --port 8000
```

### 验证

```bash
# 健康检查
curl http://localhost:8000/api/health

# KPI 卡片数据
curl http://localhost:8000/api/kpi

# 端到端：一次完整分析（SSE 流）
curl -N -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"信用卡业务上个月有什么异常？"}'
```

### 运行测试

```bash
pytest backend/tests/ -v
```

## 演示场景

埋入的异常：
- **华东 2026-03 逾期率 5.8%**（历史均值 ~3.2%，偏离 ≈13σ，critical 级）
- **华南 2026-02 / 2026-03 获客量断崖**（2800 → 1800 → 1450，偏离 ≈-7σ，high 级）

推荐演示问题：
1. "信用卡业务上个月有什么异常？"
2. "华东区逾期率为什么上升了？"
3. "对比各区域 2026-03 的获客量"

## 项目文档

- `FinSight Agent.md` — 原始设计文档（对标 Essex EARS 白皮书）
- `docs/plans/2026-04-18-finsight-agent-mvp.md` — 两天 MVP 实施计划 + 下周占位清单

## 开发路线

- **Week 1（当前）**: 后端 ReAct 循环 + 3 工具 + SSE + 基础前端
- **Week 2**: RAG 历史案例 + financial_api + 多 Provider + Human-in-the-Loop + Trace 持久化 + Docker + VPS 部署 + UI 重设计

## 目录结构

```
Finsight-agent/
├── backend/               # FastAPI 后端
│   ├── agent/            # ReAct orchestrator + prompts + pydantic models
│   ├── tools/            # sql_query / anomaly_detect / report_gen + registry
│   ├── llm/              # OpenAI 兼容 client
│   ├── db/               # SQLite 连接
│   ├── sse/              # SSE 事件序列化
│   └── tests/            # pytest 测试
├── frontend/             # React + Vite + TS（Day 2 实装）
├── scripts/
│   └── seed_data.py      # 生成模拟数据
├── data/                 # SQLite DB（gitignore）
└── docs/plans/           # 实施计划
```
