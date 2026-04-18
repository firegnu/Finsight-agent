# FinSight Agent MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** 在 2 天内交付一个可演示的金融数据分析 Agent：自然语言提问 → ReAct 推理 → 调用 SQL / 异常检测 / 报告生成工具 → SSE 流式展示推理过程 + 结构化报告 + 行动建议。下周打磨 RAG、多 Provider、HITL、Trace、Docker、VPS 部署等非核心功能。

**Architecture:** FastAPI 后端跑 ReAct 循环，通过 OpenAI 兼容接口调用本地 LM Studio 上的 Qwen3.5 35B A3B；3 个工具（Text-to-SQL、统计异常检测、结构化报告生成）通过 registry 分发；orchestrator 流式推送 8 种 SSE 事件（start / thinking / tool_call / tool_result / tool_error / final_text / report / done）到 Vite + React + TS + Tailwind 前端；前端左侧展示推理过程，右侧渲染结构化报告。

**Tech Stack:** Python 3.11+, FastAPI, OpenAI SDK (LM Studio 兼容), Pydantic v2, SQLite, NumPy; React 18 + TypeScript, Vite, Tailwind CSS.

**Design Reference:** 本 plan 基于 `FinSight Agent.md` 设计文档，经过 MVP 演示定位的取舍和收敛。设计讨论详见 conversation context。

---

## 0. 执行原则

- **Demo 优先，生产次要**：只做黄金路径，砍掉边缘情况和防御性代码。
- **Frequent commits**：每完成一个任务（Task）就 commit + push，每天结束前远程有进展。
- **TDD 仅用于纯函数**：异常检测数学、SQL 校验、Pydantic 模型用 pytest 测；LLM 集成点用 curl 人工验证；前端用浏览器人工验证。
- **文件行数弹性**：演示项目，单文件可略超 200 行，但模块职责必须清晰。
- **测试失败先停下再修**：绝不跳过或绕过失败的测试。

---

## 1. Week 2 占位契约（这两天 **不实现**，但代码中预留接口）

| 下周要加 | 这两天的占位 |
|---|---|
| RAG 历史案例 + rag_search 工具 | `tools/registry.py` 用字典模式；`AnomalyFinding.references: list[str] = []` |
| financial_api 工具 + industry_benchmark 表 | `AnomalyFinding.baseline_value: float \| None = None` |
| 多 LLM Provider 切换 | `config.py` 用 Pydantic Settings，`LLM_PROVIDER/LLM_BASE_URL/LLM_API_KEY/LLM_MODEL` 四参数化 |
| Human-in-the-Loop 真实审批 | `AnalysisReport.requires_human_review: bool` 字段；前端 `ApprovalButtons` 为假按钮（只本地 state） |
| Trace 日志持久化 | `orchestrator.py` 内存 trace 收集（不写 DB）；`TraceStep/TraceLog` 模型建好 |
| 真实 KPI 聚合 | `/api/kpi` 硬编码返回 JSON，接口契约不变 |
| Docker Compose + VPS 部署 | `requirements.txt` + `.env.example` 已备 |
| UI 视觉用 claude design 重做 | 组件结构 + className 保持清晰，不引入组件库 |

---

## 2. 风险应对速查

| 风险 | 触发条件 | 备选方案 |
|---|---|---|
| Qwen3.5 35B Tool Calling 不稳 | >30% 工具调用格式错误 | 切 Qwen3.5 27B 稠密版 |
| Text-to-SQL 失败率高 | 重试 2 次仍失败 | 退化为 4 个硬编码 SQL 模板 + 槽位填充 |
| SSE 前端断流 | fetch stream error | 加 `GET /api/analyze/result/{trace_id}` 轮询兜底 |
| Day 1 超时 | Day 1 结束 orchestrator 跑不通 | 放弃 report_gen 严格 JSON schema，改 prompt 引导 + Pydantic 宽松解析 |
| Day 2 超时 | Day 2 下午 15:00 报告面板未完成 | 砍 KPI 卡片 + 顶栏，保留推理 + 报告两块 |

---

## 3. 最终目录结构（完成时）

```
Finsight-agent/
├── README.md
├── FinSight Agent.md                # 原设计文档
├── .env.example
├── .env                             # 本地（.gitignore）
├── .gitignore
├── docs/
│   └── plans/
│       └── 2026-04-18-finsight-agent-mvp.md
├── backend/
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── prompts.py
│   │   └── models.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py
│   │   ├── sql_query.py
│   │   ├── anomaly_detect.py
│   │   └── report_gen.py
│   ├── llm/
│   │   ├── __init__.py
│   │   └── client.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py
│   └── sse/
│       ├── __init__.py
│       └── events.py
├── backend/tests/                   # pytest 目录
│   ├── test_anomaly_detect.py
│   ├── test_sql_validator.py
│   └── test_seed_data.py
├── scripts/
│   └── seed_data.py
├── data/                            # .gitignore
│   └── finsight.db
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css
        ├── types/
        │   └── index.ts
        ├── utils/
        │   └── api.ts
        ├── hooks/
        │   └── useSSE.ts
        └── components/
            ├── Header.tsx
            ├── KPICards.tsx
            ├── ChatInput.tsx
            ├── ReasoningPanel.tsx
            ├── ReportPanel.tsx
            ├── AnomalyCard.tsx
            ├── ActionItemCard.tsx
            └── ApprovalButtons.tsx
```

---

## Phase 0 — Day 0 Setup (30 min)

### Task 0.1: LM Studio 模型就绪

**步骤：**
1. 打开 LM Studio，搜索下载 `Qwen3.5-35B-A3B` MoE 模型
2. （备选）同时下载 `Qwen3.5-27B` 稠密模型
3. 切到 Developer tab → Start Server → 监听 `localhost:1234`
4. 验证：
   ```bash
   curl http://localhost:1234/v1/models
   ```
   Expected: 返回含模型 id 的 JSON 列表

### Task 0.2: Conda 环境

```bash
conda create -n finsight python=3.11 -y
conda activate finsight
cd /Users/firegnu/Developer/personal_projs/Finsight-Agent
```

### Task 0.3: Git 初始化 + 首次 push

```bash
cd /Users/firegnu/Developer/personal_projs/Finsight-Agent
git init
git branch -M main
git remote add origin git@github.com:firegnu/Finsight-agent.git
```

### Task 0.4: .gitignore

**Create:** `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
.pytest_cache/

# Node
node_modules/
dist/
.vite/

# Data
data/
*.db
*.sqlite*

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
```

**Commit:**
```bash
git add .gitignore "FinSight Agent.md" docs/plans/2026-04-18-finsight-agent-mvp.md
git commit -m "chore: init project with design doc and implementation plan"
git push -u origin main
```

---

## Phase 1 — Backend Core (Day 1, 约 8h)

### Task 1.1: 项目骨架 + 依赖 (30 min)

**Create:** `backend/requirements.txt`

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
openai>=1.30.0
numpy>=1.26.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
```

**Commands:**
```bash
mkdir -p backend/{agent,tools,llm,db,sse} backend/tests scripts data
touch backend/__init__.py backend/main.py backend/config.py
touch backend/agent/__init__.py backend/agent/{orchestrator,prompts,models}.py
touch backend/tools/__init__.py backend/tools/{registry,sql_query,anomaly_detect,report_gen}.py
touch backend/llm/__init__.py backend/llm/client.py
touch backend/db/__init__.py backend/db/database.py
touch backend/sse/__init__.py backend/sse/events.py
touch backend/tests/__init__.py
touch scripts/seed_data.py
pip install -r backend/requirements.txt
```

**Commit:**
```bash
git add backend/ scripts/
git commit -m "chore: scaffold backend directory structure"
git push
```

---

### Task 1.2: .env.example + config.py (20 min)

**Create:** `.env.example`

```
LLM_PROVIDER=lmstudio
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=lm-studio
LLM_MODEL=qwen3.5-35b-a3b
MAX_AGENT_STEPS=10
DB_PATH=./data/finsight.db
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**Command:** `cp .env.example .env`

**Create:** `backend/config.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: str = "lmstudio"
    llm_base_url: str = "http://localhost:1234/v1"
    llm_api_key: str = "lm-studio"
    llm_model: str = "qwen3.5-35b-a3b"
    max_agent_steps: int = 10
    db_path: str = "./data/finsight.db"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
```

**Verify:**
```bash
cd backend && python -c "from config import settings; print(settings.model_dump())"
```
Expected: 输出配置字典

**Commit:**
```bash
git add .env.example backend/config.py
git commit -m "feat(backend): add env config with pydantic settings"
git push
```

---

### Task 1.3: Mock 数据生成脚本 + pytest (1h)

**目标：** 生成 60 行信用卡指标数据，埋入华东 2026-03 逾期率异常、华南 2026-02~03 获客断崖。

**Step 1 — Write failing test:**

**Create:** `backend/tests/test_seed_data.py`

```python
import sqlite3
import subprocess
from pathlib import Path

import pytest


DB_PATH = Path("data/finsight_test.db")


@pytest.fixture(scope="module")
def seeded_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    subprocess.run(
        ["python", "scripts/seed_data.py", "--db-path", str(DB_PATH)],
        check=True,
    )
    conn = sqlite3.connect(DB_PATH)
    yield conn
    conn.close()
    DB_PATH.unlink()


def test_row_count_is_60(seeded_db):
    cursor = seeded_db.execute("SELECT COUNT(*) FROM credit_card_metrics")
    assert cursor.fetchone()[0] == 60


def test_regions_are_five(seeded_db):
    cursor = seeded_db.execute("SELECT DISTINCT region FROM credit_card_metrics")
    regions = {row[0] for row in cursor.fetchall()}
    assert regions == {"华东", "华南", "华北", "华西", "华中"}


def test_east_march_overdue_spike(seeded_db):
    cursor = seeded_db.execute(
        "SELECT overdue_rate FROM credit_card_metrics WHERE region=? AND year_month=?",
        ("华东", "2026-03"),
    )
    overdue = cursor.fetchone()[0]
    assert 0.055 <= overdue <= 0.060, f"Expected ~5.8%, got {overdue}"


def test_south_feb_mar_new_customers_drop(seeded_db):
    cursor = seeded_db.execute(
        "SELECT new_customers FROM credit_card_metrics WHERE region=? AND year_month IN (?, ?)",
        ("华南", "2026-02", "2026-03"),
    )
    values = [row[0] for row in cursor.fetchall()]
    assert all(v < 2000 for v in values), f"Expected <2000, got {values}"
```

**Step 2 — Run test (expect fail):**
```bash
cd /Users/firegnu/Developer/personal_projs/Finsight-Agent
python -m pytest backend/tests/test_seed_data.py -v
```
Expected: FAIL（脚本还不存在）

**Step 3 — Implement seed script:**

**Create:** `scripts/seed_data.py`

```python
"""Generate mock credit card metrics data into SQLite.

Run: python scripts/seed_data.py [--db-path ./data/finsight.db]
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import numpy as np


REGIONS = ["华东", "华南", "华北", "华西", "华中"]
MONTHS = [f"2025-{m:02d}" for m in range(4, 13)] + [f"2026-{m:02d}" for m in range(1, 4)]

SCHEMA = """
CREATE TABLE credit_card_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year_month TEXT NOT NULL,
    region TEXT NOT NULL,
    new_customers INTEGER NOT NULL,
    activation_rate REAL NOT NULL,
    monthly_transaction_volume REAL NOT NULL,
    overdue_rate REAL NOT NULL,
    collection_recovery_rate REAL NOT NULL,
    customer_complaints INTEGER NOT NULL,
    revenue_per_customer REAL NOT NULL,
    churn_rate REAL NOT NULL,
    UNIQUE(year_month, region)
);
CREATE INDEX idx_region_month ON credit_card_metrics(region, year_month);
"""

# 每区域基线（按业务合理性设定）
BASELINES = {
    "华东": {"new": 2800, "act": 0.78, "vol": 2200, "ovr": 0.032, "col": 0.86, "cpl": 120, "rpc": 680, "chn": 0.028},
    "华南": {"new": 2600, "act": 0.76, "vol": 1950, "ovr": 0.034, "col": 0.84, "cpl": 130, "rpc": 650, "chn": 0.030},
    "华北": {"new": 2400, "act": 0.80, "vol": 1800, "ovr": 0.030, "col": 0.87, "cpl": 110, "rpc": 700, "chn": 0.025},
    "华西": {"new": 1800, "act": 0.74, "vol": 1400, "ovr": 0.036, "col": 0.83, "cpl": 140, "rpc": 600, "chn": 0.032},
    "华中": {"new": 2000, "act": 0.77, "vol": 1600, "ovr": 0.033, "col": 0.85, "cpl": 125, "rpc": 640, "chn": 0.029},
}


def generate_row(region: str, month: str, rng: np.random.Generator) -> tuple:
    b = BASELINES[region]
    new_c = int(rng.normal(b["new"], b["new"] * 0.06))
    act = float(np.clip(rng.normal(b["act"], 0.015), 0.6, 0.9))
    vol = float(rng.normal(b["vol"], b["vol"] * 0.08))
    ovr = float(np.clip(rng.normal(b["ovr"], 0.002), 0.02, 0.05))
    col = float(np.clip(rng.normal(b["col"], 0.015), 0.75, 0.95))
    cpl = int(rng.normal(b["cpl"], 12))
    rpc = float(rng.normal(b["rpc"], 25))
    chn = float(np.clip(rng.normal(b["chn"], 0.003), 0.015, 0.05))
    return (month, region, new_c, act, vol, ovr, col, cpl, rpc, chn)


def apply_anomalies(rows: list[tuple]) -> list[tuple]:
    """Inject engineered anomalies into the dataset."""
    result = []
    for row in rows:
        month, region, new_c, act, vol, ovr, col, cpl, rpc, chn = row
        # 华东 2026-03 逾期率飙升 + 投诉量 +40% + 催收率 -5%
        if region == "华东" and month == "2026-03":
            ovr = 0.058
            cpl = int(cpl * 1.4)
            col = col - 0.05
        # 华南 2026-02 获客 1800, 2026-03 获客 1450 + 激活率同步走低
        if region == "华南" and month == "2026-02":
            new_c = 1800
            act = act - 0.04
        if region == "华南" and month == "2026-03":
            new_c = 1450
            act = act - 0.06
        result.append((month, region, new_c, act, vol, ovr, col, cpl, rpc, chn))
    return result


def seed(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    rng = np.random.default_rng(seed=42)
    rows = [generate_row(r, m, rng) for r in REGIONS for m in MONTHS]
    rows = apply_anomalies(rows)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT INTO credit_card_metrics "
            "(year_month, region, new_customers, activation_rate, monthly_transaction_volume, "
            " overdue_rate, collection_recovery_rate, customer_complaints, "
            " revenue_per_customer, churn_rate) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            rows,
        )
        conn.commit()
        print(f"✓ Seeded {len(rows)} rows into {db_path}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default="./data/finsight.db")
    args = parser.parse_args()
    seed(Path(args.db_path))


if __name__ == "__main__":
    main()
```

**Step 4 — Run test (expect pass):**
```bash
python -m pytest backend/tests/test_seed_data.py -v
```
Expected: 4 PASS

**Step 5 — Generate production DB:**
```bash
python scripts/seed_data.py
sqlite3 data/finsight.db "SELECT region, year_month, overdue_rate FROM credit_card_metrics WHERE region='华东' ORDER BY year_month;"
```
Expected: 华东 2026-03 应显示 ~0.058

**Commit:**
```bash
git add scripts/seed_data.py backend/tests/test_seed_data.py
git commit -m "feat(data): seed script with engineered anomalies for demo"
git push
```

---

### Task 1.4: Database module + FastAPI 骨架 + health check (30 min)

**Create:** `backend/db/database.py`

```python
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from ..config import settings


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    db_path = Path(settings.db_path)
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run: python scripts/seed_data.py"
        )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def query_all(sql: str, params: tuple = ()) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
```

**Create:** `backend/main.py`

```python
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("finsight")

app = FastAPI(title="FinSight Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "model": settings.llm_model, "provider": settings.llm_provider}
```

**Verify:**
```bash
cd /Users/firegnu/Developer/personal_projs/Finsight-Agent
uvicorn backend.main:app --reload --port 8000
```
In another shell:
```bash
curl http://localhost:8000/api/health
```
Expected: `{"status":"ok","model":"qwen3.5-35b-a3b","provider":"lmstudio"}`

Ctrl+C to stop.

**Commit:**
```bash
git add backend/db/database.py backend/main.py
git commit -m "feat(backend): FastAPI app + health check + db helper"
git push
```

---

### Task 1.5: /api/kpi 硬编码接口 (20 min)

**Modify:** `backend/main.py` — append at the end

```python
@app.get("/api/kpi")
async def kpi() -> dict:
    """Hardcoded KPI dashboard data (week 2: aggregate from SQLite)."""
    return {
        "period": "2026-03",
        "updated_at": "2026-04-18T09:00:00Z",
        "metrics": [
            {"name": "获客量", "value": "12,450", "change": "+5.2%", "trend": "up", "alert": False},
            {"name": "激活率", "value": "78.3%", "change": "-1.1%", "trend": "down", "alert": False},
            {"name": "交易额", "value": "8,230万", "change": "+3.4%", "trend": "up", "alert": False},
            {"name": "逾期率", "value": "3.8%", "change": "+0.6%", "trend": "up", "alert": True},
            {"name": "催收回收率", "value": "85.2%", "change": "-2.1%", "trend": "down", "alert": False},
        ],
    }
```

**Verify:**
```bash
uvicorn backend.main:app --reload --port 8000  # 另一终端
curl http://localhost:8000/api/kpi | python -m json.tool
```
Expected: 含 5 张 metric 卡的 JSON

**Commit:**
```bash
git add backend/main.py
git commit -m "feat(backend): add hardcoded /api/kpi endpoint"
git push
```

---

### Task 1.6: LLM Client (20 min)

**Create:** `backend/llm/client.py`

```python
from openai import AsyncOpenAI

from ..config import settings


def make_client() -> AsyncOpenAI:
    """OpenAI-compatible client. Points to LM Studio locally; week 2 switches base_url for DeepSeek/Qwen online."""
    return AsyncOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )


llm = make_client()
MODEL = settings.llm_model
```

**Verify:** 快速烟测（确保 LM Studio server 已启动）

```bash
python -c "
import asyncio
from backend.llm.client import llm, MODEL

async def main():
    r = await llm.chat.completions.create(
        model=MODEL,
        messages=[{'role': 'user', 'content': '用一句话介绍你自己'}],
    )
    print(r.choices[0].message.content)

asyncio.run(main())
"
```
Expected: Qwen 的自我介绍

**Commit:**
```bash
git add backend/llm/client.py
git commit -m "feat(llm): OpenAI-compatible client pointing to LM Studio"
git push
```

---

### Task 1.7: Pydantic 数据模型 (30 min)

**Create:** `backend/agent/models.py`

```python
from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class AnomalyFinding(BaseModel):
    metric: str
    region: str
    period: str
    current_value: float
    historical_mean: float
    historical_std: float
    deviation_sigma: float
    baseline_value: float | None = None  # week 2: financial_api 提供行业基准
    severity: Literal["low", "medium", "high", "critical"]
    root_cause_hypothesis: str = ""
    references: list[str] = []  # week 2: RAG 案例引用


class ActionItem(BaseModel):
    title: str
    description: str
    priority: Literal["P0", "P1", "P2", "P3"]
    expected_impact: str
    owner_suggestion: str
    deadline_suggestion: str


class AnalysisReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"rpt-{uuid4().hex[:8]}")
    trace_id: str = Field(default_factory=lambda: f"trace-{uuid4().hex[:12]}")
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    period: str
    executive_summary: str
    key_findings: list[str]
    anomalies: list[AnomalyFinding]
    action_items: list[ActionItem]
    data_sources: list[str]
    requires_human_review: bool = False


# Week 2 Trace (现在只在内存中收集，不入库)
class TraceStep(BaseModel):
    step_number: int
    action_type: Literal["llm_reasoning", "tool_call", "tool_result", "tool_error"]
    tool_name: str | None = None
    tool_input: dict | None = None
    tool_output_summary: str | None = None
    latency_ms: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class TraceLog(BaseModel):
    trace_id: str
    user_query: str
    steps: list[TraceStep] = []
    final_report: AnalysisReport | None = None
    total_latency_ms: int = 0
    llm_model: str
    status: Literal["success", "error", "running"] = "running"
```

**Commit:**
```bash
git add backend/agent/models.py
git commit -m "feat(agent): pydantic models with week-2 placeholder fields"
git push
```

---

### Task 1.8: System Prompt + 字段元数据 (30 min)

**Create:** `backend/agent/prompts.py`

```python
"""Agent system prompt + field metadata (hardcoded; week 2 moves to RAG)."""

FIELD_METADATA = [
    {"field": "new_customers", "name_cn": "新客获客量", "synonyms": ["获客", "新客", "新用户"], "unit": "人"},
    {"field": "activation_rate", "name_cn": "激活率", "synonyms": ["激活", "开卡率"], "unit": "比例 0-1"},
    {"field": "monthly_transaction_volume", "name_cn": "月交易额", "synonyms": ["交易额", "GMV"], "unit": "万元"},
    {"field": "overdue_rate", "name_cn": "逾期率", "synonyms": ["不良率", "违约率", "delinquency"], "unit": "比例 0-1", "alert_threshold": 0.05},
    {"field": "collection_recovery_rate", "name_cn": "催收回收率", "synonyms": ["催收率", "回收率"], "unit": "比例 0-1"},
    {"field": "customer_complaints", "name_cn": "客户投诉量", "synonyms": ["投诉", "complaints"], "unit": "件"},
    {"field": "revenue_per_customer", "name_cn": "客均收入", "synonyms": ["ARPU", "人均收入"], "unit": "元"},
    {"field": "churn_rate", "name_cn": "流失率", "synonyms": ["流失", "用户流失"], "unit": "比例 0-1"},
    {"field": "region", "name_cn": "区域", "synonyms": ["大区", "地区"], "values": ["华东", "华南", "华北", "华西", "华中"]},
    {"field": "year_month", "name_cn": "年月", "synonyms": ["月份", "期间"], "format": "YYYY-MM"},
]


SYSTEM_PROMPT = """你是 FinSight，一个金融数据分析 Agent，服务于零售银行的信用卡业务主管。
你的核心理念是「从数据到洞察到行动」——不只是展示数字，而是分析数字背后的含义并给出可执行的建议。

# 你的工具
1. **sql_query** — 查询内部业务数据（信用卡月度指标，按区域汇总）
2. **anomaly_detect** — 对指标做统计异常检测（历史均值 ± 标准差）
3. **report_gen** — 生成最终结构化报告（必须在最后一步调用）

# 分析流程
1. 收到问题 → 说明你的思考（一两句话）
2. 调用 sql_query 获取相关数据
3. 调用 anomaly_detect 发现异常
4. 基于异常数据和业务常识，用 CoT 推理根因
5. 调用 report_gen 生成结构化报告

根据用户问题灵活调整，不必每次都走完整流程。每调用一次工具前，先简短说明你打算做什么、为什么。

# 关键约束
- **所有数字必须来自工具返回，绝不估算或编造**
- 工具失败时告知用户原因，不用编造数据替代
- 异常严重度为 high / critical 时，报告中 requires_human_review=true
- 每个发现注明数据来源（data_sources 字段）
- 只提供数据分析和运营改进建议，不给投资建议

# 可用字段（信用卡月度指标表 credit_card_metrics）
{fields_json}

# 数据时间范围
2025-04 至 2026-03，按月度 × 5 个区域汇总（华东/华南/华北/华西/华中）
""".format(fields_json=str(FIELD_METADATA))


SQL_GEN_PROMPT = """你是 SQL 生成器。只输出一条 SQLite SELECT 语句，不要解释，不要 markdown 代码块。
只有一张表 credit_card_metrics，字段如下：
{fields}

规则：
- 只生成 SELECT 语句，禁止 INSERT/UPDATE/DELETE/DROP/CREATE
- 日期字段 year_month 格式为 'YYYY-MM' 文本，用字符串比较
- 聚合时注意 GROUP BY
- 百分比字段（activation_rate / overdue_rate 等）已经是 0-1 小数，不要再除 100

# Few-shot 示例

用户：华东最近 3 个月的逾期率
SQL: SELECT year_month, overdue_rate FROM credit_card_metrics WHERE region='华东' AND year_month >= '2026-01' ORDER BY year_month;

用户：各区域 2026-03 的获客量对比
SQL: SELECT region, new_customers FROM credit_card_metrics WHERE year_month='2026-03' ORDER BY new_customers DESC;

用户：全国 2026-03 的平均逾期率
SQL: SELECT AVG(overdue_rate) AS avg_overdue FROM credit_card_metrics WHERE year_month='2026-03';

用户：过去 12 个月华南的月度交易额趋势
SQL: SELECT year_month, monthly_transaction_volume FROM credit_card_metrics WHERE region='华南' ORDER BY year_month;
""".format(fields=str(FIELD_METADATA))
```

**Commit:**
```bash
git add backend/agent/prompts.py
git commit -m "feat(agent): system prompt + field metadata + SQL gen prompt"
git push
```

---

### Task 1.9: SSE 事件定义 (15 min)

**Create:** `backend/sse/events.py`

```python
import json
from typing import Any, Literal

from pydantic import BaseModel


EventType = Literal[
    "start", "thinking", "tool_call", "tool_result",
    "tool_error", "final_text", "report", "done", "error",
]


class SSEEvent(BaseModel):
    type: EventType
    data: dict[str, Any] = {}

    def serialize(self) -> str:
        payload = json.dumps(self.model_dump(), ensure_ascii=False, default=str)
        return f"data: {payload}\n\n"
```

**Commit:**
```bash
git add backend/sse/events.py
git commit -m "feat(sse): event schema + serialization"
git push
```

---

### Task 1.10: SQL 校验器 + sql_query 工具 (1.5h)

**目标：** Text-to-SQL with safety validator + retry.

**Step 1 — Write failing test:**

**Create:** `backend/tests/test_sql_validator.py`

```python
import pytest
from backend.tools.sql_query import validate_sql_readonly, SQLValidationError


def test_accepts_simple_select():
    validate_sql_readonly("SELECT * FROM credit_card_metrics")


def test_accepts_select_with_where():
    validate_sql_readonly("SELECT year_month FROM credit_card_metrics WHERE region='华东'")


def test_accepts_aggregate():
    validate_sql_readonly("SELECT region, AVG(overdue_rate) FROM credit_card_metrics GROUP BY region")


def test_rejects_insert():
    with pytest.raises(SQLValidationError):
        validate_sql_readonly("INSERT INTO credit_card_metrics VALUES (1)")


def test_rejects_update():
    with pytest.raises(SQLValidationError):
        validate_sql_readonly("UPDATE credit_card_metrics SET overdue_rate=0")


def test_rejects_delete():
    with pytest.raises(SQLValidationError):
        validate_sql_readonly("DELETE FROM credit_card_metrics")


def test_rejects_drop():
    with pytest.raises(SQLValidationError):
        validate_sql_readonly("DROP TABLE credit_card_metrics")


def test_rejects_multiple_statements():
    with pytest.raises(SQLValidationError):
        validate_sql_readonly("SELECT 1; DELETE FROM credit_card_metrics")


def test_rejects_attach():
    with pytest.raises(SQLValidationError):
        validate_sql_readonly("ATTACH DATABASE 'foo.db' AS bar")
```

**Step 2 — Run (expect fail):** `python -m pytest backend/tests/test_sql_validator.py -v`

**Step 3 — Implement `backend/tools/sql_query.py`:**

```python
"""Text-to-SQL tool with safety validator + retry."""
from __future__ import annotations

import logging
import re

from ..db.database import query_all
from ..llm.client import llm, MODEL
from ..agent.prompts import SQL_GEN_PROMPT

logger = logging.getLogger("finsight.sql_query")

MAX_RETRIES = 2
MAX_ROWS_RETURNED = 200


class SQLValidationError(ValueError):
    pass


FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|DETACH|PRAGMA|REPLACE)\b",
    re.IGNORECASE,
)


def validate_sql_readonly(sql: str) -> None:
    stripped = sql.strip().rstrip(";")
    if ";" in stripped:
        raise SQLValidationError("Multiple statements not allowed")
    if not re.match(r"^\s*SELECT\b", stripped, re.IGNORECASE):
        raise SQLValidationError("Only SELECT statements allowed")
    if FORBIDDEN.search(stripped):
        raise SQLValidationError(f"Forbidden keyword detected in: {sql[:80]}")


async def generate_sql(query_description: str, prior_error: str | None = None) -> str:
    user_msg = f"用户需求：{query_description}"
    if prior_error:
        user_msg += f"\n\n上次生成的 SQL 执行出错了：{prior_error}\n请修正后重新生成。"

    response = await llm.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SQL_GEN_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0,
    )
    raw = response.choices[0].message.content or ""
    sql = raw.strip()
    # 去掉常见的 markdown fence
    sql = re.sub(r"^```(?:sql)?\s*", "", sql)
    sql = re.sub(r"\s*```\s*$", "", sql)
    return sql.strip().rstrip(";")


async def run(query_description: str) -> dict:
    """Tool entry point: natural-language description → SQL → rows."""
    last_err: str | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            sql = await generate_sql(query_description, prior_error=last_err)
            validate_sql_readonly(sql)
            rows = query_all(sql)
            if len(rows) > MAX_ROWS_RETURNED:
                rows = rows[:MAX_ROWS_RETURNED]
            logger.info("sql_query success on attempt %d: %s", attempt + 1, sql)
            return {"sql": sql, "row_count": len(rows), "rows": rows}
        except (SQLValidationError, Exception) as e:
            last_err = f"{type(e).__name__}: {e}"
            logger.warning("sql_query attempt %d failed: %s", attempt + 1, last_err)
            if attempt == MAX_RETRIES:
                return {"error": last_err, "sql_attempted": locals().get("sql", "<not generated>")}
    return {"error": "unreachable"}


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "sql_query",
        "description": (
            "查询信用卡业务数据库。用于获客量、激活率、交易额、逾期率、催收回收率、"
            "投诉量、客均收入、流失率等指标查询。只有一张表 credit_card_metrics。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query_description": {
                    "type": "string",
                    "description": "自然语言描述要查的数据，如 '华东区最近3个月的逾期率'",
                }
            },
            "required": ["query_description"],
        },
    },
}
```

**Step 4 — Run tests (expect pass):** `python -m pytest backend/tests/test_sql_validator.py -v`

**Step 5 — Smoke test (requires LM Studio running):**

```bash
python -c "
import asyncio
from backend.tools.sql_query import run
print(asyncio.run(run('华东最近3个月的逾期率')))
"
```
Expected: 返回 `{"sql": "...", "row_count": 3, "rows": [...]}`

**Commit:**
```bash
git add backend/tools/sql_query.py backend/tests/test_sql_validator.py
git commit -m "feat(tools): sql_query with safety validator and retry"
git push
```

---

### Task 1.11: anomaly_detect 工具 (1h)

**Step 1 — Test file:**

**Create:** `backend/tests/test_anomaly_detect.py`

```python
import pytest

from backend.tools.anomaly_detect import compute_anomaly, SeverityThresholds


def test_no_anomaly_within_2_sigma():
    result = compute_anomaly(current=3.3, mean=3.2, std=0.2)
    assert result["severity"] == "low"
    assert result["is_anomaly"] is False


def test_medium_anomaly_at_2_sigma():
    result = compute_anomaly(current=3.65, mean=3.2, std=0.2)
    # deviation = 2.25σ
    assert result["severity"] == "medium"
    assert result["is_anomaly"] is True


def test_high_anomaly_above_2_5_sigma():
    result = compute_anomaly(current=3.8, mean=3.2, std=0.2)
    # deviation = 3σ
    assert result["severity"] in ("high", "critical")
    assert result["is_anomaly"] is True


def test_critical_anomaly_above_3_sigma():
    result = compute_anomaly(current=5.8, mean=3.2, std=0.2)
    # deviation = 13σ
    assert result["severity"] == "critical"
    assert result["is_anomaly"] is True


def test_zero_std_handled():
    result = compute_anomaly(current=3.2, mean=3.2, std=0.0)
    assert result["is_anomaly"] is False
```

**Step 2 — Run (expect fail)**

**Step 3 — Implement `backend/tools/anomaly_detect.py`:**

```python
"""Statistical anomaly detection over historical mean ± std."""
from __future__ import annotations

import logging
import re
import statistics
from typing import Literal

from ..db.database import query_all

logger = logging.getLogger("finsight.anomaly_detect")


METRICS_ENUM = [
    "overdue_rate", "activation_rate", "churn_rate", "collection_recovery_rate",
    "new_customers", "revenue_per_customer", "monthly_transaction_volume",
    "customer_complaints", "all",
]

_METRICS_ALL = [m for m in METRICS_ENUM if m != "all"]


class SeverityThresholds:
    MEDIUM = 2.0
    HIGH = 2.5
    CRITICAL = 3.0


def compute_anomaly(current: float, mean: float, std: float) -> dict:
    if std == 0:
        return {"is_anomaly": False, "deviation_sigma": 0.0, "severity": "low"}
    deviation = abs(current - mean) / std
    if deviation >= SeverityThresholds.CRITICAL:
        severity = "critical"
    elif deviation >= SeverityThresholds.HIGH:
        severity = "high"
    elif deviation >= SeverityThresholds.MEDIUM:
        severity = "medium"
    else:
        severity = "low"
    return {
        "is_anomaly": severity != "low",
        "deviation_sigma": round(deviation, 2),
        "severity": severity,
    }


def _parse_period(period: str) -> tuple[str, str] | None:
    """Return (start_month, end_month) inclusive. None = all history (for baseline)."""
    if re.match(r"^\d{4}-\d{2}$", period):
        return (period, period)
    if period == "recent_3_months":
        return ("2026-01", "2026-03")
    if period == "recent_6_months":
        return ("2025-10", "2026-03")
    return None


def _detect_for_metric(metric: str, start: str, end: str) -> list[dict]:
    rows = query_all(
        f"SELECT region, year_month, {metric} AS value FROM credit_card_metrics ORDER BY region, year_month"
    )
    by_region: dict[str, list[tuple[str, float]]] = {}
    for r in rows:
        by_region.setdefault(r["region"], []).append((r["year_month"], r["value"]))

    findings: list[dict] = []
    for region, series in by_region.items():
        history = [v for m, v in series if m < start]
        current_window = [(m, v) for m, v in series if start <= m <= end]
        if len(history) < 3 or not current_window:
            continue
        mean = statistics.mean(history)
        std = statistics.stdev(history) if len(history) >= 2 else 0.0
        for month, value in current_window:
            stat = compute_anomaly(value, mean, std)
            if stat["is_anomaly"]:
                findings.append({
                    "metric": metric,
                    "region": region,
                    "period": month,
                    "current_value": round(value, 4),
                    "historical_mean": round(mean, 4),
                    "historical_std": round(std, 4),
                    "deviation_sigma": stat["deviation_sigma"],
                    "severity": stat["severity"],
                })
    return findings


async def run(metric: str = "all", period: str = "recent_3_months") -> dict:
    parsed = _parse_period(period)
    if not parsed:
        return {"error": f"Unknown period: {period}"}
    start, end = parsed

    metrics = _METRICS_ALL if metric == "all" else [metric]
    all_findings: list[dict] = []
    for m in metrics:
        all_findings.extend(_detect_for_metric(m, start, end))

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_findings.sort(key=lambda f: (severity_rank[f["severity"]], -f["deviation_sigma"]))

    logger.info("anomaly_detect found %d anomalies for metric=%s period=%s", len(all_findings), metric, period)
    return {
        "period": period,
        "metric_requested": metric,
        "anomaly_count": len(all_findings),
        "findings": all_findings,
    }


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "anomaly_detect",
        "description": (
            "对信用卡业务指标进行异常检测，对比历史均值和标准差，标记严重度。"
            "自动查询数据库，不需要先调用 sql_query。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {"type": "string", "enum": METRICS_ENUM, "description": "要检测的指标，'all' 表示全部"},
                "period": {
                    "type": "string",
                    "description": "检测时间范围，如 '2026-03' 或 'recent_3_months' 或 'recent_6_months'",
                    "default": "recent_3_months",
                },
            },
            "required": ["metric"],
        },
    },
}
```

**Step 4 — Run tests (expect pass):** `python -m pytest backend/tests/ -v`

**Step 5 — Smoke test:**
```bash
python -c "
import asyncio
from backend.tools.anomaly_detect import run
print(asyncio.run(run('overdue_rate', '2026-03')))
"
```
Expected: 华东 2026-03 critical 异常出现

**Commit:**
```bash
git add backend/tools/anomaly_detect.py backend/tests/test_anomaly_detect.py
git commit -m "feat(tools): anomaly_detect with statistical severity scoring"
git push
```

---

### Task 1.12: report_gen 工具 (45 min)

**Create:** `backend/tools/report_gen.py`

```python
"""Structured report generator using Pydantic schema + JSON mode."""
from __future__ import annotations

import json
import logging
from uuid import uuid4

from pydantic import ValidationError

from ..agent.models import AnalysisReport
from ..llm.client import llm, MODEL

logger = logging.getLogger("finsight.report_gen")

MAX_RETRIES = 1


REPORT_SYS_PROMPT = """你是报告生成器。基于用户提供的分析发现，生成一份结构化 JSON 报告。

严格遵守以下 JSON schema（字段不可省略，缺失则用空字符串或空列表）：

{
  "period": "string，如 '2026-03' 或 'recent_3_months'",
  "executive_summary": "string，2-3 句话概括最重要的发现",
  "key_findings": ["string", ...],
  "anomalies": [
    {
      "metric": "string",
      "region": "string",
      "period": "string",
      "current_value": number,
      "historical_mean": number,
      "historical_std": number,
      "deviation_sigma": number,
      "baseline_value": null,
      "severity": "low | medium | high | critical",
      "root_cause_hypothesis": "string，基于数据和业务常识的根因推测",
      "references": []
    }, ...
  ],
  "action_items": [
    {
      "title": "string，简洁",
      "description": "string，具体可执行",
      "priority": "P0 | P1 | P2 | P3",
      "expected_impact": "string",
      "owner_suggestion": "string，如 '风控部负责人'",
      "deadline_suggestion": "string，如 '7 天内' 或 '2026-04-30'"
    }, ...
  ],
  "data_sources": ["string，如 'credit_card_metrics 表 2025-04~2026-03'"],
  "requires_human_review": true | false
}

规则：
- severity 为 high/critical 时，requires_human_review=true
- 每个异常至少配一个行动建议
- 只输出 JSON，不要任何解释、markdown 代码块
- 数字字段保持原始精度
"""


async def run(findings_summary: str) -> dict:
    """Generate structured report from prior findings."""
    last_err: str | None = None
    for attempt in range(MAX_RETRIES + 1):
        user_msg = f"分析发现：\n{findings_summary}"
        if last_err:
            user_msg += f"\n\n上次生成的 JSON 有错误：{last_err}\n请修正后重新生成。"

        response = await llm.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": REPORT_SYS_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        try:
            parsed = json.loads(raw)
            # 补默认值
            parsed.setdefault("report_id", f"rpt-{uuid4().hex[:8]}")
            parsed.setdefault("trace_id", f"trace-{uuid4().hex[:12]}")
            report = AnalysisReport(**parsed)
            logger.info("report_gen success on attempt %d", attempt + 1)
            return report.model_dump()
        except (json.JSONDecodeError, ValidationError) as e:
            last_err = f"{type(e).__name__}: {str(e)[:300]}"
            logger.warning("report_gen attempt %d failed: %s", attempt + 1, last_err)

    return {"error": f"report_gen failed after {MAX_RETRIES + 1} attempts: {last_err}"}


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "report_gen",
        "description": (
            "生成最终结构化分析报告（含执行摘要、异常项、行动建议）。"
            "必须在完成 sql_query 和 anomaly_detect 等数据采集后作为最后一步调用。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "findings_summary": {
                    "type": "string",
                    "description": "前序工具调用的发现汇总（JSON 字符串或自然语言总结均可）",
                }
            },
            "required": ["findings_summary"],
        },
    },
}
```

**Commit:**
```bash
git add backend/tools/report_gen.py
git commit -m "feat(tools): report_gen with pydantic validation"
git push
```

---

### Task 1.13: Tool Registry (15 min)

**Create:** `backend/tools/registry.py`

```python
"""Tool registry — add new tools by appending to the two dicts below."""
from typing import Any, Awaitable, Callable

from . import anomaly_detect, report_gen, sql_query


ToolHandler = Callable[..., Awaitable[dict]]


TOOL_DEFINITIONS: list[dict] = [
    sql_query.TOOL_SCHEMA,
    anomaly_detect.TOOL_SCHEMA,
    report_gen.TOOL_SCHEMA,
]


TOOL_HANDLERS: dict[str, ToolHandler] = {
    "sql_query": sql_query.run,
    "anomaly_detect": anomaly_detect.run,
    "report_gen": report_gen.run,
}


async def execute_tool(name: str, args: dict[str, Any]) -> dict:
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return {"error": f"Unknown tool: {name}"}
    return await handler(**args)
```

**Commit:**
```bash
git add backend/tools/registry.py backend/tools/__init__.py
git commit -m "feat(tools): registry for pluggable tool dispatch"
git push
```

---

### Task 1.14: ReAct Orchestrator (1h)

**Create:** `backend/agent/orchestrator.py`

```python
"""ReAct loop with SSE event streaming."""
from __future__ import annotations

import json
import logging
import time
from typing import AsyncGenerator
from uuid import uuid4

from ..config import settings
from ..llm.client import llm, MODEL
from ..sse.events import SSEEvent
from ..tools.registry import TOOL_DEFINITIONS, execute_tool
from .models import TraceLog, TraceStep
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger("finsight.orchestrator")

MAX_TOOL_RESULT_SUMMARY = 500


def _summarize_tool_result(name: str, result: dict) -> str:
    """Short summary for SSE display."""
    if "error" in result:
        return f"❌ {result['error'][:200]}"
    if name == "sql_query":
        return f"✅ 执行 SQL，返回 {result.get('row_count', 0)} 行"
    if name == "anomaly_detect":
        return f"✅ 检测完成，发现 {result.get('anomaly_count', 0)} 个异常"
    if name == "report_gen":
        return f"✅ 报告生成完成（{len(result.get('anomalies', []))} 异常 / {len(result.get('action_items', []))} 建议）"
    return f"✅ {str(result)[:MAX_TOOL_RESULT_SUMMARY]}"


async def run_agent(user_query: str) -> AsyncGenerator[SSEEvent, None]:
    trace = TraceLog(
        trace_id=f"trace-{uuid4().hex[:12]}",
        user_query=user_query,
        llm_model=MODEL,
    )
    t_start = time.time()

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]

    yield SSEEvent(type="start", data={"trace_id": trace.trace_id, "query": user_query})

    for step in range(settings.max_agent_steps):
        step_t = time.time()
        try:
            response = await llm.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.3,
            )
        except Exception as e:
            logger.exception("LLM call failed at step %d", step)
            yield SSEEvent(type="error", data={"msg": f"LLM call failed: {e}"})
            trace.status = "error"
            return

        msg = response.choices[0].message

        if msg.content:
            yield SSEEvent(type="thinking", data={"content": msg.content, "step": step})
            trace.steps.append(TraceStep(
                step_number=step, action_type="llm_reasoning",
                tool_output_summary=msg.content[:MAX_TOOL_RESULT_SUMMARY],
                latency_ms=int((time.time() - step_t) * 1000),
            ))

        if not msg.tool_calls:
            yield SSEEvent(type="final_text", data={"content": msg.content or ""})
            trace.status = "success"
            break

        # 有工具调用 — 追加 assistant message（带 tool_calls）
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
        })

        report_was_called = False
        report_result: dict | None = None

        for tc in msg.tool_calls:
            tool_name = tc.function.name
            try:
                tool_args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                tool_args = {}

            yield SSEEvent(type="tool_call", data={
                "name": tool_name, "args": tool_args, "step": step,
            })
            tool_t = time.time()
            result = await execute_tool(tool_name, tool_args)

            if "error" in result and tool_name != "report_gen":
                yield SSEEvent(type="tool_error", data={
                    "name": tool_name, "error": result["error"], "step": step,
                })
            else:
                yield SSEEvent(type="tool_result", data={
                    "name": tool_name,
                    "summary": _summarize_tool_result(tool_name, result),
                    "step": step,
                })

            trace.steps.append(TraceStep(
                step_number=step, action_type="tool_call",
                tool_name=tool_name, tool_input=tool_args,
                tool_output_summary=_summarize_tool_result(tool_name, result),
                latency_ms=int((time.time() - tool_t) * 1000),
            ))

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False, default=str)[:20000],
            })

            if tool_name == "report_gen" and "error" not in result:
                report_was_called = True
                report_result = result

        if report_was_called and report_result:
            yield SSEEvent(type="report", data=report_result)
            trace.status = "success"
            break
    else:
        yield SSEEvent(type="error", data={"msg": f"Reached max steps ({settings.max_agent_steps})"})
        trace.status = "error"

    trace.total_latency_ms = int((time.time() - t_start) * 1000)
    yield SSEEvent(type="done", data={"trace_id": trace.trace_id, "total_latency_ms": trace.total_latency_ms})
```

**Commit:**
```bash
git add backend/agent/orchestrator.py backend/agent/__init__.py
git commit -m "feat(agent): ReAct orchestrator with SSE streaming"
git push
```

---

### Task 1.15: /api/analyze SSE endpoint (30 min)

**Modify:** `backend/main.py` — append

```python
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .agent.orchestrator import run_agent


class AnalyzeRequest(BaseModel):
    query: str


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest) -> StreamingResponse:
    async def stream():
        async for event in run_agent(req.query):
            yield event.serialize()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
```

**Verify — end-to-end (requires LM Studio + seed data):**
```bash
uvicorn backend.main:app --reload --port 8000
```
Another shell:
```bash
curl -N -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"信用卡业务上个月有什么异常？"}'
```
Expected: 流式输出 `data: {...}` 事件，最后看到 `type: "report"` 完整 JSON，然后 `type: "done"`

**Commit:**
```bash
git add backend/main.py
git commit -m "feat(api): add /api/analyze SSE endpoint"
git push
```

---

### Task 1.16: Day 1 验收 + README 占位 (15 min)

**Create:** `README.md`

```markdown
# FinSight Agent

金融数据智能分析 Agent（MVP 演示项目）——用户用自然语言提问，Agent 自动从多数据源采集数据、检测异常、生成带有优先级的行动建议报告。

## 快速启动

### 前置条件
- Python 3.11+（建议 conda env）
- Node.js 20+
- LM Studio（启动 server 监听 localhost:1234，加载 Qwen3.5 35B A3B）

### 后端

    # 1. 安装依赖
    pip install -r backend/requirements.txt

    # 2. 配置环境变量
    cp .env.example .env

    # 3. 生成模拟数据
    python scripts/seed_data.py

    # 4. 启动 API 服务器
    uvicorn backend.main:app --reload --port 8000

### 前端

    cd frontend
    npm install
    npm run dev     # http://localhost:5173

### 验证

    curl http://localhost:8000/api/health
    curl -N -X POST http://localhost:8000/api/analyze \
      -H "Content-Type: application/json" \
      -d '{"query":"信用卡业务上个月有什么异常？"}'

## 架构

见 `FinSight Agent.md`（设计文档）与 `docs/plans/2026-04-18-finsight-agent-mvp.md`（实施计划）。

## 开发路线

- **Week 1（这两天）**: 后端 ReAct 循环 + 3 工具（sql_query / anomaly_detect / report_gen） + SSE + 基础前端
- **Week 2**: RAG 历史案例 + financial_api + 多 Provider + Human-in-the-Loop + Trace 持久化 + Docker + VPS 部署 + UI 重设计
```

**Run full test suite:**
```bash
python -m pytest backend/tests/ -v
```
Expected: all tests PASS

**Commit:**
```bash
git add README.md
git commit -m "docs: add README with quickstart"
git push
```

**Day 1 Checklist:**
- [x] LM Studio 可调用
- [x] 60 行 mock 数据入库
- [x] `/api/health` 200
- [x] `/api/kpi` 返回硬编码 KPI
- [x] `/api/analyze` 端到端跑通完整 SSE 流
- [x] 3 个工具通过 pytest 或 smoke test
- [x] 所有代码已 push GitHub

---

## Phase 2 — Frontend (Day 2, 约 8h)

### Task 2.1: Vite 脚手架 (45 min)

**Commands:**
```bash
cd /Users/firegnu/Developer/personal_projs/Finsight-Agent
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install -D tailwindcss@^3 postcss autoprefixer
npx tailwindcss init -p
```

**Modify:** `frontend/tailwind.config.js`

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
  plugins: [],
};
```

**Modify:** `frontend/src/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html, body, #root { height: 100%; margin: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; }
```

**Modify:** `frontend/vite.config.ts` — 加代理

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
});
```

**Verify:**
```bash
npm run dev
```
Expected: 浏览器打开 http://localhost:5173，看到 Vite 默认页

**Commit:**
```bash
cd ..
git add frontend/
git commit -m "chore(frontend): Vite + React + TS + Tailwind scaffold"
git push
```

---

### Task 2.2: TypeScript 类型 + API 工具 (30 min)

**Create:** `frontend/src/types/index.ts`

```typescript
export type EventType =
  | "start" | "thinking" | "tool_call" | "tool_result"
  | "tool_error" | "final_text" | "report" | "done" | "error";

export interface SSEEvent {
  type: EventType;
  data: Record<string, any>;
}

export interface AnomalyFinding {
  metric: string;
  region: string;
  period: string;
  current_value: number;
  historical_mean: number;
  historical_std: number;
  deviation_sigma: number;
  baseline_value: number | null;
  severity: "low" | "medium" | "high" | "critical";
  root_cause_hypothesis: string;
  references: string[];
}

export interface ActionItem {
  title: string;
  description: string;
  priority: "P0" | "P1" | "P2" | "P3";
  expected_impact: string;
  owner_suggestion: string;
  deadline_suggestion: string;
}

export interface AnalysisReport {
  report_id: string;
  trace_id: string;
  generated_at: string;
  period: string;
  executive_summary: string;
  key_findings: string[];
  anomalies: AnomalyFinding[];
  action_items: ActionItem[];
  data_sources: string[];
  requires_human_review: boolean;
}

export interface KPIMetric {
  name: string;
  value: string;
  change: string;
  trend: "up" | "down" | "flat";
  alert: boolean;
}

export interface KPIResponse {
  period: string;
  updated_at: string;
  metrics: KPIMetric[];
}
```

**Create:** `frontend/src/utils/api.ts`

```typescript
import type { KPIResponse } from "../types";

export async function fetchKPI(): Promise<KPIResponse> {
  const r = await fetch("/api/kpi");
  if (!r.ok) throw new Error(`KPI fetch failed: ${r.status}`);
  return r.json();
}
```

**Commit:**
```bash
git add frontend/src/types frontend/src/utils
git commit -m "feat(frontend): types + api helpers"
git push
```

---

### Task 2.3: useSSE Hook (45 min)

**Create:** `frontend/src/hooks/useSSE.ts`

```typescript
import { useCallback, useRef, useState } from "react";
import type { SSEEvent } from "../types";

type Status = "idle" | "running" | "done" | "error";

export function useSSE() {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    setEvents([]);
    setError(null);
    setStatus("idle");
  }, []);

  const analyze = useCallback(async (query: string) => {
    reset();
    setStatus("running");
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      const resp = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
        signal: ctrl.signal,
      });
      if (!resp.ok || !resp.body) throw new Error(`analyze failed: ${resp.status}`);

      const reader = resp.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // SSE 按 "\n\n" 分隔事件
        let idx: number;
        while ((idx = buffer.indexOf("\n\n")) !== -1) {
          const raw = buffer.slice(0, idx).trim();
          buffer = buffer.slice(idx + 2);
          if (!raw.startsWith("data:")) continue;
          const json = raw.replace(/^data:\s*/, "");
          try {
            const event = JSON.parse(json) as SSEEvent;
            setEvents((prev) => [...prev, event]);
            if (event.type === "done") setStatus("done");
            if (event.type === "error") {
              setStatus("error");
              setError(event.data?.msg || "Unknown error");
            }
          } catch (e) {
            console.warn("Bad SSE payload:", json);
          }
        }
      }
      if (status === "running") setStatus("done");
    } catch (e: any) {
      if (e.name !== "AbortError") {
        setStatus("error");
        setError(e.message);
      }
    }
  }, [reset, status]);

  const abort = useCallback(() => {
    abortRef.current?.abort();
    setStatus("idle");
  }, []);

  return { events, status, error, analyze, abort, reset };
}
```

**Commit:**
```bash
git add frontend/src/hooks
git commit -m "feat(frontend): useSSE hook with fetch stream"
git push
```

---

### Task 2.4: App 骨架 + 布局 (30 min)

**Replace:** `frontend/src/App.tsx`

```tsx
import { useMemo, useState } from "react";
import { Header } from "./components/Header";
import { KPICards } from "./components/KPICards";
import { ChatInput } from "./components/ChatInput";
import { ReasoningPanel } from "./components/ReasoningPanel";
import { ReportPanel } from "./components/ReportPanel";
import { useSSE } from "./hooks/useSSE";
import type { AnalysisReport } from "./types";

export default function App() {
  const { events, status, error, analyze } = useSSE();
  const [input, setInput] = useState("");

  const report = useMemo<AnalysisReport | null>(() => {
    const rpt = [...events].reverse().find((e) => e.type === "report");
    return rpt ? (rpt.data as AnalysisReport) : null;
  }, [events]);

  const onSend = () => {
    if (!input.trim() || status === "running") return;
    analyze(input.trim());
  };

  return (
    <div className="h-full flex flex-col bg-slate-50">
      <Header />
      <div className="flex-none p-4 border-b border-slate-200 bg-white">
        <KPICards />
      </div>
      <div className="flex-1 flex min-h-0">
        <div className="w-2/5 border-r border-slate-200 bg-white overflow-hidden">
          <ReasoningPanel events={events} status={status} error={error} />
        </div>
        <div className="flex-1 overflow-hidden">
          <ReportPanel report={report} status={status} />
        </div>
      </div>
      <div className="flex-none p-4 border-t border-slate-200 bg-white">
        <ChatInput
          value={input}
          onChange={setInput}
          onSend={onSend}
          disabled={status === "running"}
        />
      </div>
    </div>
  );
}
```

**Replace:** `frontend/src/main.tsx`

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

**Create stub components first (so App compiles):**

**Create:** `frontend/src/components/Header.tsx`

```tsx
export function Header() {
  return (
    <header className="flex items-center justify-between px-6 h-14 border-b border-slate-200 bg-white">
      <h1 className="text-lg font-semibold text-slate-800">FinSight Agent</h1>
      <div className="text-sm text-slate-500">Model: Qwen3.5-35B-A3B (local)</div>
    </header>
  );
}
```

**Create:** `frontend/src/components/KPICards.tsx`

```tsx
import { useEffect, useState } from "react";
import type { KPIResponse } from "../types";
import { fetchKPI } from "../utils/api";

export function KPICards() {
  const [kpi, setKpi] = useState<KPIResponse | null>(null);

  useEffect(() => {
    fetchKPI().then(setKpi).catch(console.error);
  }, []);

  if (!kpi) return <div className="text-sm text-slate-400">加载指标中...</div>;

  return (
    <div className="grid grid-cols-5 gap-3">
      {kpi.metrics.map((m) => (
        <div
          key={m.name}
          className={`rounded-lg p-3 border ${
            m.alert ? "border-red-300 bg-red-50" : "border-slate-200 bg-white"
          }`}
        >
          <div className="text-xs text-slate-500">{m.name}</div>
          <div className="text-xl font-semibold text-slate-800 mt-1">{m.value}</div>
          <div className={`text-xs mt-1 ${m.trend === "up" ? "text-red-600" : "text-green-600"}`}>
            {m.change} {m.trend === "up" ? "↑" : "↓"}
          </div>
        </div>
      ))}
    </div>
  );
}
```

**Create:** `frontend/src/components/ChatInput.tsx`

```tsx
interface Props {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled: boolean;
}

export function ChatInput({ value, onChange, onSend, disabled }: Props) {
  return (
    <div className="flex gap-2">
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) onSend(); }}
        placeholder="💬 请输入分析需求，如：信用卡业务上个月有什么异常？"
        className="flex-1 border border-slate-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
        disabled={disabled}
      />
      <button
        onClick={onSend}
        disabled={disabled || !value.trim()}
        className="px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:bg-slate-300"
      >
        {disabled ? "分析中..." : "发送"}
      </button>
    </div>
  );
}
```

**Create stubs for ReasoningPanel/ReportPanel** (filled in next tasks):

**Create:** `frontend/src/components/ReasoningPanel.tsx`

```tsx
import type { SSEEvent } from "../types";

interface Props {
  events: SSEEvent[];
  status: string;
  error: string | null;
}

export function ReasoningPanel({ events, status, error }: Props) {
  return (
    <div className="h-full p-4 overflow-auto">
      <h2 className="text-sm font-semibold text-slate-600 mb-3">Agent 推理过程</h2>
      <div className="text-xs text-slate-400">status: {status} · events: {events.length}</div>
      {error && <div className="text-red-500 text-sm mt-2">{error}</div>}
    </div>
  );
}
```

**Create:** `frontend/src/components/ReportPanel.tsx`

```tsx
import type { AnalysisReport } from "../types";

interface Props {
  report: AnalysisReport | null;
  status: string;
}

export function ReportPanel({ report, status }: Props) {
  return (
    <div className="h-full p-4 overflow-auto">
      <h2 className="text-sm font-semibold text-slate-600 mb-3">分析报告</h2>
      {!report && <div className="text-sm text-slate-400">等待分析完成...</div>}
      {report && <pre className="text-xs">{JSON.stringify(report, null, 2)}</pre>}
    </div>
  );
}
```

**Verify:**
```bash
cd frontend && npm run dev
```
Expected: 页面能看到顶栏 + KPI 卡（5 张，逾期率高亮红色）+ 左右两栏 + 底部输入框

**Commit:**
```bash
cd ..
git add frontend/src
git commit -m "feat(frontend): app layout skeleton with stub components"
git push
```

---

### Task 2.5: ReasoningPanel 完整实现 (1h)

**Replace:** `frontend/src/components/ReasoningPanel.tsx`

```tsx
import { useEffect, useRef } from "react";
import type { SSEEvent } from "../types";

interface Props {
  events: SSEEvent[];
  status: string;
  error: string | null;
}

export function ReasoningPanel({ events, status, error }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [events.length]);

  return (
    <div className="h-full flex flex-col">
      <div className="flex-none px-4 py-3 border-b border-slate-200 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-700">🧠 Agent 推理过程</h2>
        <StatusPill status={status} />
      </div>
      <div ref={scrollRef} className="flex-1 overflow-auto p-4 space-y-2">
        {events.length === 0 && !error && (
          <div className="text-sm text-slate-400 italic">
            等待输入分析需求...
          </div>
        )}
        {events.map((e, i) => (
          <EventItem key={i} event={e} />
        ))}
        {error && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">
            ⚠️ {error}
          </div>
        )}
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const cfg: Record<string, { label: string; cls: string }> = {
    idle: { label: "就绪", cls: "bg-slate-100 text-slate-600" },
    running: { label: "● 运行中", cls: "bg-blue-100 text-blue-700 animate-pulse" },
    done: { label: "✓ 完成", cls: "bg-green-100 text-green-700" },
    error: { label: "✗ 错误", cls: "bg-red-100 text-red-700" },
  };
  const c = cfg[status] || cfg.idle;
  return <span className={`text-xs px-2 py-0.5 rounded ${c.cls}`}>{c.label}</span>;
}

function EventItem({ event }: { event: SSEEvent }) {
  switch (event.type) {
    case "start":
      return (
        <div className="text-xs text-slate-500">
          🚀 开始分析: <span className="font-medium">{event.data.query}</span>
        </div>
      );
    case "thinking":
      return (
        <div className="text-sm text-slate-600 italic border-l-2 border-slate-300 pl-3 py-1">
          💭 {event.data.content}
        </div>
      );
    case "tool_call":
      return (
        <div className="text-sm bg-blue-50 border border-blue-200 rounded p-2">
          🔧 调用工具 <span className="font-mono font-semibold">{event.data.name}</span>
          <pre className="text-xs text-slate-500 mt-1 whitespace-pre-wrap break-all">
            {JSON.stringify(event.data.args, null, 2)}
          </pre>
        </div>
      );
    case "tool_result":
      return (
        <div className="text-sm text-green-700 bg-green-50 border border-green-200 rounded p-2">
          {event.data.summary}
        </div>
      );
    case "tool_error":
      return (
        <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
          ❌ {event.data.name} 失败: {event.data.error}
        </div>
      );
    case "final_text":
      return (
        <div className="text-sm text-slate-800 bg-slate-100 rounded p-2 whitespace-pre-wrap">
          {event.data.content}
        </div>
      );
    case "report":
      return (
        <div className="text-xs text-slate-500">📝 报告已生成，见右侧面板</div>
      );
    case "done":
      return (
        <div className="text-xs text-slate-400">
          ✓ 完成 · 总耗时 {event.data.total_latency_ms}ms
        </div>
      );
    case "error":
      return null; // 顶部错误条会显示
    default:
      return null;
  }
}
```

**Verify:** `npm run dev` → 发起提问 → 左侧面板应逐条出现事件

**Commit:**
```bash
git add frontend/src/components/ReasoningPanel.tsx
git commit -m "feat(frontend): reasoning panel with typed event rendering"
git push
```

---

### Task 2.6: AnomalyCard + ActionItemCard (45 min)

**Create:** `frontend/src/components/AnomalyCard.tsx`

```tsx
import type { AnomalyFinding } from "../types";

const SEVERITY_STYLE: Record<AnomalyFinding["severity"], string> = {
  critical: "bg-red-100 border-red-400 text-red-800",
  high: "bg-orange-100 border-orange-400 text-orange-800",
  medium: "bg-yellow-100 border-yellow-400 text-yellow-800",
  low: "bg-blue-100 border-blue-400 text-blue-800",
};

const SEVERITY_EMOJI: Record<AnomalyFinding["severity"], string> = {
  critical: "🔴",
  high: "🟠",
  medium: "🟡",
  low: "🔵",
};

function formatValue(metric: string, value: number): string {
  if (metric.includes("rate")) return `${(value * 100).toFixed(2)}%`;
  if (metric.includes("customers") || metric.includes("complaints")) return value.toLocaleString();
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export function AnomalyCard({ anomaly }: { anomaly: AnomalyFinding }) {
  return (
    <div className={`border rounded-lg p-3 ${SEVERITY_STYLE[anomaly.severity]}`}>
      <div className="flex items-center justify-between">
        <div className="font-semibold">
          {SEVERITY_EMOJI[anomaly.severity]} {anomaly.region} · {anomaly.metric}
        </div>
        <div className="text-xs uppercase tracking-wide font-medium">
          {anomaly.severity}
        </div>
      </div>
      <div className="text-sm mt-2 space-y-1">
        <div>
          期间: <span className="font-mono">{anomaly.period}</span>
        </div>
        <div>
          当前值:{" "}
          <span className="font-semibold">{formatValue(anomaly.metric, anomaly.current_value)}</span>
          {"  "}·{"  "}
          历史均值:{" "}
          <span className="font-mono">{formatValue(anomaly.metric, anomaly.historical_mean)}</span>
          {"  "}·{"  "}
          偏离: <span className="font-semibold">{anomaly.deviation_sigma}σ</span>
        </div>
        {anomaly.root_cause_hypothesis && (
          <div className="text-xs mt-2 bg-white/50 p-2 rounded">
            <span className="font-semibold">根因推测:</span> {anomaly.root_cause_hypothesis}
          </div>
        )}
      </div>
    </div>
  );
}
```

**Create:** `frontend/src/components/ActionItemCard.tsx`

```tsx
import type { ActionItem } from "../types";

const PRIORITY_STYLE: Record<ActionItem["priority"], string> = {
  P0: "bg-red-600 text-white",
  P1: "bg-orange-500 text-white",
  P2: "bg-blue-500 text-white",
  P3: "bg-slate-400 text-white",
};

export function ActionItemCard({ item }: { item: ActionItem }) {
  return (
    <div className="border border-slate-200 rounded-lg p-3 bg-white">
      <div className="flex items-center gap-2">
        <span className={`text-xs font-semibold px-2 py-0.5 rounded ${PRIORITY_STYLE[item.priority]}`}>
          {item.priority}
        </span>
        <h3 className="font-semibold text-slate-800 text-sm">{item.title}</h3>
      </div>
      <p className="text-sm text-slate-600 mt-2">{item.description}</p>
      <div className="grid grid-cols-3 gap-2 mt-3 text-xs text-slate-500">
        <div>
          <div className="font-semibold text-slate-600">预期影响</div>
          <div>{item.expected_impact}</div>
        </div>
        <div>
          <div className="font-semibold text-slate-600">建议负责人</div>
          <div>{item.owner_suggestion}</div>
        </div>
        <div>
          <div className="font-semibold text-slate-600">截止时间</div>
          <div>{item.deadline_suggestion}</div>
        </div>
      </div>
    </div>
  );
}
```

**Commit:**
```bash
git add frontend/src/components/AnomalyCard.tsx frontend/src/components/ActionItemCard.tsx
git commit -m "feat(frontend): anomaly card + action item card components"
git push
```

---

### Task 2.7: ApprovalButtons + ReportPanel 完整实现 (1h)

**Create:** `frontend/src/components/ApprovalButtons.tsx`

```tsx
import { useState } from "react";

interface Props {
  reportId: string;
  requiresReview: boolean;
}

type Decision = "pending" | "approved" | "rejected";

export function ApprovalButtons({ reportId, requiresReview }: Props) {
  const [decision, setDecision] = useState<Decision>("pending");

  if (!requiresReview) {
    return (
      <div className="text-xs text-slate-500">✓ 此报告无需人工审批</div>
    );
  }

  if (decision !== "pending") {
    return (
      <div
        className={`text-sm font-semibold ${
          decision === "approved" ? "text-green-700" : "text-red-700"
        }`}
      >
        {decision === "approved" ? "✓ 已批准" : "✗ 已驳回"}
      </div>
    );
  }

  return (
    <div className="flex gap-2">
      <button
        onClick={() => setDecision("approved")}
        className="px-4 py-1.5 text-sm rounded bg-green-600 text-white hover:bg-green-700"
      >
        ✓ 批准执行
      </button>
      <button
        onClick={() => setDecision("rejected")}
        className="px-4 py-1.5 text-sm rounded bg-red-100 text-red-700 hover:bg-red-200"
      >
        ✗ 驳回
      </button>
      <span className="text-xs text-slate-400 self-center ml-2">
        (week 2 接入真实审批 API)
      </span>
    </div>
  );
}
```

**Replace:** `frontend/src/components/ReportPanel.tsx`

```tsx
import type { AnalysisReport } from "../types";
import { AnomalyCard } from "./AnomalyCard";
import { ActionItemCard } from "./ActionItemCard";
import { ApprovalButtons } from "./ApprovalButtons";

interface Props {
  report: AnalysisReport | null;
  status: string;
}

export function ReportPanel({ report, status }: Props) {
  if (!report) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400">
        {status === "running"
          ? "🔍 正在生成报告..."
          : "📋 等待分析结果"}
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-none px-4 py-3 border-b border-slate-200 flex items-center justify-between bg-white">
        <div>
          <h2 className="text-sm font-semibold text-slate-700">📊 分析报告</h2>
          <div className="text-xs text-slate-400 mt-0.5">
            期间: {report.period} · Report ID: {report.report_id}
          </div>
        </div>
        {report.requires_human_review && (
          <span className="text-xs px-2 py-0.5 rounded bg-orange-100 text-orange-700 font-medium">
            需人工审批
          </span>
        )}
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-5">
        <section>
          <h3 className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-2">
            执行摘要
          </h3>
          <p className="text-sm text-slate-800 leading-relaxed bg-slate-50 p-3 rounded-lg">
            {report.executive_summary}
          </p>
        </section>

        {report.key_findings.length > 0 && (
          <section>
            <h3 className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-2">
              关键发现
            </h3>
            <ul className="text-sm text-slate-700 space-y-1 list-disc list-inside">
              {report.key_findings.map((f, i) => <li key={i}>{f}</li>)}
            </ul>
          </section>
        )}

        {report.anomalies.length > 0 && (
          <section>
            <h3 className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-2">
              异常项 ({report.anomalies.length})
            </h3>
            <div className="space-y-2">
              {report.anomalies.map((a, i) => <AnomalyCard key={i} anomaly={a} />)}
            </div>
          </section>
        )}

        {report.action_items.length > 0 && (
          <section>
            <h3 className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-2">
              行动建议 ({report.action_items.length})
            </h3>
            <div className="space-y-2">
              {report.action_items.map((a, i) => <ActionItemCard key={i} item={a} />)}
            </div>
          </section>
        )}

        {report.data_sources.length > 0 && (
          <section className="text-xs text-slate-500">
            <span className="font-semibold">数据来源：</span>
            {report.data_sources.join(" · ")}
          </section>
        )}
      </div>

      <div className="flex-none px-4 py-3 border-t border-slate-200 bg-slate-50">
        <ApprovalButtons
          reportId={report.report_id}
          requiresReview={report.requires_human_review}
        />
      </div>
    </div>
  );
}
```

**Verify:** `npm run dev` → 提问后右侧报告面板应完整渲染（摘要 + 关键发现 + 异常卡片 + 行动卡片 + 审批区）

**Commit:**
```bash
git add frontend/src/components
git commit -m "feat(frontend): complete report panel with anomaly/action cards"
git push
```

---

### Task 2.8: 端到端演示验证 (45 min)

**启动 3 个终端：**
1. `cd ...Finsight-Agent && uvicorn backend.main:app --reload --port 8000`
2. `cd ...Finsight-Agent/frontend && npm run dev`
3. 留作 `curl` / 日志观察

**测试问题清单（在浏览器 http://localhost:5173 依次输入）：**

| # | 问题 | 预期结果 |
|---|---|---|
| 1 | 信用卡业务上个月有什么异常？ | 华东逾期率 critical + 华南获客 high，至少 2 个 P0/P1 建议 |
| 2 | 华东区逾期率为什么上升了？ | sql_query 查华东历史 + anomaly_detect + 根因假设 |
| 3 | 对比各区域 2026-03 的交易额 | 纯 sql_query，无异常，输出柱状摘要 |

**手动检查清单：**
- [ ] 输入后输入框禁用、按钮变"分析中..."
- [ ] 左侧面板逐条出现 thinking / tool_call / tool_result
- [ ] 工具调用参数可见、摘要人类可读
- [ ] 右侧面板在 report 事件到达时渲染完整报告
- [ ] severity 颜色正确（critical 红 / high 橙 / medium 黄 / low 蓝）
- [ ] 优先级徽章颜色正确（P0 深红 / P1 橙 / P2 蓝 / P3 灰）
- [ ] requires_human_review=true 时审批按钮可点，切换本地状态
- [ ] 全流程无 console error

**发现问题的修法：**
- 工具调用失败 → 查 uvicorn 日志、LM Studio 日志
- SSE 断流 → 浏览器 Network tab 看 `/api/analyze` 响应流
- JSON 校验失败 → report_gen 会自动重试 1 次；仍失败时看 `SYSTEM_PROMPT` 是否太严
- Qwen 乱说中文 → temperature 降到 0.1，或切 27B 稠密版

**Commit（如果有修复）：**
```bash
git commit -am "fix: e2e demo polish"
git push
```

---

### Task 2.9: README 完善 + 启动脚本 (30 min)

**Create:** `Makefile`（可选，简化常用命令）

```makefile
.PHONY: seed dev-backend dev-frontend test install

install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

seed:
	python scripts/seed_data.py

dev-backend:
	uvicorn backend.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	python -m pytest backend/tests/ -v
```

**Update README.md**：加演示截图位、演示脚本、技术深挖 FAQ（抄设计文档 8.3）。

**Commit:**
```bash
git add Makefile README.md
git commit -m "docs: add Makefile and expand README"
git push
```

---

### Task 2.10: Day 2 收尾（录屏 + 最终 push）(15 min)

**最终验证：**
```bash
# 1. 重建 DB 确保可重复
rm -f data/finsight.db
python scripts/seed_data.py

# 2. 全部测试过
python -m pytest backend/tests/ -v

# 3. 后端 + 前端启动
make dev-backend   # 终端 1
make dev-frontend  # 终端 2

# 4. 浏览器录屏演示 3 个问题
```

**录屏：** 用 macOS 自带 QuickTime / ScreenFlow 录 2-3 分钟演示，保存到本地（不入库）。

**Day 2 Checklist:**
- [x] 前端布局 + 组件全部实现
- [x] SSE 端到端可用
- [x] 3 个演示问题流畅跑通
- [x] README 可照着启动
- [x] 所有代码已 push GitHub
- [x] 有可用的演示录屏

**Final commit:**
```bash
git tag v0.1.0-demo -m "MVP demo ready for showcase"
git push --tags
```

---

## 4. 下周任务列表（仅占位，**本次不做**）

### Week 2 优先级

1. **RAG 历史案例库**（高优先，技术叙事关键）
   - 写 3-5 个 markdown 案例（华东 2024 Q3 逾期率事件、审批门槛调整案例等）
   - Chroma 本地索引 + indexer 脚本
   - `rag_search` 工具注册到 registry
   - System prompt 加"遇到异常先检索历史案例"指令
   - `AnomalyFinding.references` 填入案例 id

2. **financial_api 工具 + 行业基准表**
   - 加 `industry_benchmark` 表（5-10 个指标）
   - `AnomalyFinding.baseline_value` 填入行业值
   - AnomalyCard UI 显示"行业基准 vs 当前值"

3. **多 LLM Provider 切换**
   - `.env` 多套配置
   - UI 顶栏模型下拉（从占位改成真切换）
   - DeepSeek / Qwen 在线 API 接入（VPS 部署必备）

4. **Human-in-the-Loop 真实审批**
   - `POST /api/approve/{report_id}` 端点
   - SQLite `approvals` 表持久化决策
   - UI 审批按钮接 API

5. **Trace 日志持久化 + 查看页**
   - `/api/traces` 列表 + `/api/traces/{id}` 详情
   - 前端新增 `/traces` 路由 + 页面

6. **Docker Compose 一键启动**
   - `backend/Dockerfile` + `frontend/Dockerfile`
   - `docker-compose.yml`

7. **VPS 部署**
   - 阿里云/腾讯云轻量 + Docker + Nginx 反向代理
   - HTTPS（Let's Encrypt）
   - 线上演示链接

8. **UI 重设计（claude design）**
   - 把这两天的裸 Tailwind 换成 polished 视觉
   - 加动效（推理面板 streaming、报告 section 淡入）

9. **真实 KPI 聚合**
   - `/api/kpi` 改为从 SQLite 最新月份实时聚合

10. **Claude Code Skills（`.claude/skills/`）**
    - **格式参考**：Anthropic 官方开源的 `anthropics/financial-services-plugins` 里的 `SKILL.md` 格式（YAML frontmatter + markdown 流程文档）
    - **领域适配**：官方 plugin 聚焦投行建模（DCF/LBO/comps），不直接用；我们面向零售银行运营监控，自写针对性 skills
    - **预计产出 5-7 个 skills**，两大类：
      - *开发工作流 skills*：
        - `add-new-tool.md` — 给 Agent 加新工具的约定（对齐 `tools/registry.py`）
        - `switch-provider.md` — 切换 LLM provider 的 checklist
        - `debug-sse.md` — SSE 断流排查
        - `deploy-vps.md` — VPS 部署步骤（Task 7 完成后落地）
      - *业务方法论 skills*（Agent 可查阅的领域知识）：
        - `anomaly-investigation.md` — 异常检测后的调查步骤
        - `root-cause-reasoning.md` — 根因推理框架（观察 → 假设 → 验证）
        - `cohort-comparison.md` — 区域/客群对比分析方法
    - **在 README 和项目展示时明确**：本项目的 skills 参考 Anthropic 官方 financial-services-plugins 的格式约定做领域适配（投行建模 → 零售银行运营监控），体现对生态 + 设计哲学 + 领域落地的综合理解
    - **工时**：~2h

### Week 2 推荐执行顺序

```
Day 3: #1 RAG 历史案例库                  (P0，最大叙事升级)
Day 4: #2 financial_api + #9 真实 KPI     (两个快赢，~3h)
Day 5: #6 Docker Compose                  (为 VPS 做准备)
Day 6: #7 VPS 部署 + #3 Provider 切换     (合在一起：线上一切就绪)
Day 7: #4 HITL + #5 Trace 持久化 + #10 Skills (打磨 + 加分项)
Day 8+: #8 UI 视觉升级                    (Claude Design 主导)
```

---

## 5. 执行约定

- **每个 Task 结束必须 commit + push**，不要积压
- **测试失败先修复再继续**，不要跳过
- **LLM 调用前确认 LM Studio server 还活着**（有时会 idle 掉）
- **遇到设计之外的需求变更，先停下讨论，不要擅自扩展范围**
- **时间超支触发 Risk Mitigation 表的 fallback**
