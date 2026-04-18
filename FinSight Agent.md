## 项目代号：FinSight Agent

------

## 一、项目定位

### 1.1 一句话描述

金融数据智能分析Agent——用户用自然语言提问，Agent自动从多数据源采集数据、检测异常、追溯根因、生成带有优先级排序的行动建议报告。

### 1.2 核心能力矩阵

| 本项目功能                     | 能力类型                    | 核心技术                  |
| ------------------------------ | -------------------------- | ------------------------- |
| 自然语言→SQL生成→执行→结果解释 | 自然语言查询                | Tool Calling, Text-to-SQL |
| 多数据源采集                   | 统一数据层                  | Financial API + SQL + RAG |
| 异常检测 + 严重度评分          | 异常检测                    | 统计对比 + 阈值检测       |
| 根因分析                       | 根因推理                    | CoT推理 + RAG检索历史案例 |
| 结构化行动建议                 | 任务输出                    | Structured Output (JSON)  |
| 阈值预警                       | 规则预警                    | 规则引擎                  |
| 实时推理展示                   | 流式 UI                     | SSE流式传输               |
| 人工审批                       | Human-in-the-Loop          | 审批网关                  |

### 1.3 演示场景

用户角色：零售银行信用卡业务主管

典型提问：

- "信用卡业务上个月表现怎么样？有没有异常？"
- "华东区逾期率为什么上升了？"
- "对比一下各区域的催收回收率，给我改进建议"
- "最近三个月的客户流失趋势如何？"

------

## 二、整体架构

### 2.1 架构总览

```
┌─────────────────────────────────────────────────────┐
│                Frontend (React + TypeScript)          │
│                                                       │
│  ┌─────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ 输入区   │  │ 推理过程面板  │  │ 报告 + 审批面板 │  │
│  │自然语言  │  │ SSE实时流    │  │ 行动建议列表   │  │
│  │问题输入  │  │ Step-by-step │  │ 异常高亮      │  │
│  └─────────┘  └──────────────┘  └────────────────┘  │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │              指标概览卡片 (KPI Cards)             │  │
│  │  获客量 | 激活率 | 交易额 | 逾期率 | 催收率 | ... │  │
│  └─────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP REST + SSE
                       ▼
┌─────────────────────────────────────────────────────┐
│                Backend (FastAPI)                      │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │            Outer Harness（外层编排）              │  │
│  │  ├── 请求接收 + 意图路由                          │  │
│  │  ├── Agent生命周期管理                            │  │
│  │  ├── 错误恢复 + 重试策略                          │  │
│  │  ├── Trace日志记录                               │  │
│  │  └── Human-in-the-Loop 网关                      │  │
│  └──────────────────┬──────────────────────────────┘  │
│                     │                                  │
│  ┌──────────────────▼──────────────────────────────┐  │
│  │            Inner Harness（ReAct推理循环）          │  │
│  │  Observe → Think → Act → Observe → ...           │  │
│  │  ├── Prompt组装（System + RAG上下文 + 用户输入）   │  │
│  │  ├── 工具选择 + 参数生成                          │  │
│  │  ├── 工具执行 + 结果观察                          │  │
│  │  └── 输出解析 + Pydantic验证                     │  │
│  └──────────────────┬──────────────────────────────┘  │
│                     │                                  │
│  ┌──────────────────▼──────────────────────────────┐  │
│  │              Tool Registry (5个工具)              │  │
│  │                                                   │  │
│  │  ┌─────────────┐  ┌──────────────────┐           │  │
│  │  │ sql_query   │  │ financial_api    │           │  │
│  │  │ Text-to-SQL │  │ 行业基准数据查询  │           │  │
│  │  └─────────────┘  └──────────────────┘           │  │
│  │  ┌─────────────┐  ┌──────────────────┐           │  │
│  │  │ rag_search  │  │ anomaly_detect   │           │  │
│  │  │ 知识库检索   │  │ 异常检测+评分     │           │  │
│  │  └─────────────┘  └──────────────────┘           │  │
│  │  ┌─────────────┐                                  │  │
│  │  │ report_gen  │                                  │  │
│  │  │ 报告生成     │                                  │  │
│  │  └─────────────┘                                  │  │
│  └───────────────────────────────────────────────────┘  │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │          LLM Provider Layer（统一接口层）          │  │
│  │  OpenAI / Claude / DeepSeek / Qwen (本地)        │  │
│  │  统一OpenAI兼容接口，配置文件切换                  │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
│  ┌──────────────┐  ┌────────────────────────────┐    │
│  │ Knowledge    │  │ Storage & Trace            │    │
│  │ Base (RAG)   │  │                            │    │
│  │ 元数据知识库  │  │ SQLite：业务数据            │    │
│  │ + 历史案例   │  │ SQLite：分析记录 + Trace    │    │
│  │ → Chroma     │  │                            │    │
│  └──────────────┘  └────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 2.2 技术选型

| 层次       | 技术选择                          | 选择理由                               |
| ---------- | --------------------------------- | -------------------------------------- |
| 前端框架   | React 18 + TypeScript             | JD要求，团队标准栈                     |
| 前端样式   | Tailwind CSS                      | 快速开发，组件化                       |
| 后端框架   | FastAPI                           | 原生async，SSE支持好，类型提示         |
| LLM接口    | OpenAI Python SDK                 | 统一接口，兼容多Provider               |
| 向量数据库 | Chroma                            | 零配置，pip install即用，适合演示      |
| 业务数据库 | SQLite                            | 零配置，单文件，演示足够               |
| Embedding  | text-embedding-3-small 或 本地BGE | 按网络环境选择                         |
| 流式传输   | SSE (Server-Sent Events)          | 单向推送，比WebSocket简单              |
| 数据验证   | Pydantic v2                       | FastAPI原生集成，Structured Output验证 |
| 容器化     | Docker + Docker Compose           | 一键部署                               |

------

## 三、模块详细设计

### 3.1 模拟数据设计

用Python脚本生成模拟数据，存入SQLite。

**表结构：credit_card_metrics**

| 字段                       | 类型    | 说明                           |
| -------------------------- | ------- | ------------------------------ |
| id                         | INTEGER | 主键                           |
| year_month                 | TEXT    | 年月，如 "2026-01"             |
| region                     | TEXT    | 区域：华东/华南/华北/华西/华中 |
| new_customers              | INTEGER | 新客获客量                     |
| activation_rate            | REAL    | 激活率 (0-1)                   |
| monthly_transaction_volume | REAL    | 月交易额（万元）               |
| overdue_rate               | REAL    | 逾期率 (0-1)                   |
| collection_recovery_rate   | REAL    | 催收回收率 (0-1)               |
| customer_complaints        | INTEGER | 客户投诉量                     |
| revenue_per_customer       | REAL    | 客均收入（元）                 |
| churn_rate                 | REAL    | 流失率 (0-1)                   |

数据规模：12个月 × 5个区域 = 60行

关键：在华东区2026-03埋入逾期率异常飙升（从3.2%跳到5.8%），在华南区埋入获客量下降异常。让Agent能检测到这些异常。

**表结构：industry_benchmark**

| 字段            | 类型 | 说明       |
| --------------- | ---- | ---------- |
| metric_name     | TEXT | 指标名     |
| benchmark_value | REAL | 行业基准值 |
| source          | TEXT | 数据来源   |
| updated_at      | TEXT | 更新时间   |

### 3.2 Knowledge Base 设计

参照业界数据分析 Agent 的元数据分层实践，构建三层元数据 Management Layer：

**Layer 1: 数据级上下文**

```json
{
  "tables": [
    {
      "name": "credit_card_metrics",
      "description": "信用卡业务月度核心指标，按区域汇总",
      "granularity": "月度 × 区域",
      "time_range": "2025-04 至 2026-03",
      "row_count": 60
    }
  ]
}
```

**Layer 2: 字段级元数据**

```json
{
  "fields": [
    {
      "field_name": "overdue_rate",
      "business_name": "逾期率",
      "description": "当月逾期金额占总应收金额的比例",
      "synonyms": ["不良率", "违约率", "delinquency rate"],
      "aggregation": "加权平均（按区域交易额加权）",
      "alert_threshold": 0.05,
      "unit": "百分比"
    }
  ]
}
```

**Layer 3: 业务上下文**

```json
{
  "business_rules": [
    {
      "term": "财年",
      "definition": "本系统约定财年等同于日历年（1月-12月）",
    },
    {
      "term": "健康逾期率",
      "definition": "行业标准为3%-4%，超过5%需要预警"
    }
  ]
}
```

这些元数据向量化后存入Chroma，Agent通过RAG检索获取相关字段定义来生成正确的SQL。

**历史案例库**（同样存入Chroma）：

```markdown
## 案例：华东区2024Q3逾期率异常上升

背景：华东区逾期率从3.1%上升至5.2%，环比增长67%。
根因：Q2放宽了信用评分审批门槛（从680降至650），
导致大量低信用客户进入，3个月后开始出现逾期。
应对措施：
1. 立即收紧审批标准至680
2. 对650-680分段客户启动专项催收
3. 3个月后逾期率回落至3.5%
教训：审批标准调整后需要3-6个月才能在逾期率上体现。
```

### 3.3 工具详细设计

### 工具一：sql_query（Text-to-SQL）

```python
tool_description = {
    "name": "sql_query",
    "description": """查询信用卡业务数据库。
    使用场景：用户询问业务指标数据时调用，如获客量、逾期率、交易额等。
    不要用于：查询行业基准数据（用financial_api）、
    查询历史案例和最佳实践（用rag_search）。
    数据库中只有credit_card_metrics表。""",
    "parameters": {
        "query_description": {
            "type": "string",
            "description": "用自然语言描述需要查询的数据，如'华东区最近3个月的逾期率'"
        }
    }
}
```

工作流程：

1. Agent调用sql_query，传入自然语言描述
2. 工具内部用RAG检索相关字段元数据
3. 将元数据 + 查询描述组装prompt，让LLM生成SQL
4. 执行SQL，返回结果
5. 如果SQL执行报错，自动将错误信息反馈给LLM重新生成（最多重试2次）

### 工具二：financial_api（行业基准查询）

```python
tool_description = {
    "name": "financial_api",
    "description": """查询金融行业基准数据和市场参考指标。
    使用场景：需要行业对比数据时调用，如行业平均逾期率、获客成本基准等。
    不要用于：查询内部业务数据（用sql_query）。""",
    "parameters": {
        "metric_name": {
            "type": "string",
            "enum": ["overdue_rate", "activation_rate", "churn_rate",
                     "collection_rate", "revenue_per_customer"],
            "description": "要查询的行业基准指标"
        }
    }
}
```

实现：直接查industry_benchmark表。如果要展示外部API能力，可以额外接Alpha Vantage查一个股票价格作为"市场环境参考"。

### 工具三：rag_search（知识库检索）

```python
tool_description = {
    "name": "rag_search",
    "description": """检索领域知识库，包含历史分析案例、业务规则和最佳实践。
    使用场景：需要历史对照、根因分析参考、应对策略建议时调用。
    不要用于：查询具体业务数据（用sql_query）。""",
    "parameters": {
        "query": {
            "type": "string",
            "description": "检索查询，如'逾期率上升的常见原因和应对策略'"
        },
        "top_k": {
            "type": "integer",
            "description": "返回结果数量，默认3",
            "default": 3
        }
    }
}
```

### 工具四：anomaly_detect（异常检测）

```python
tool_description = {
    "name": "anomaly_detect",
    "description": """对业务指标进行异常检测，对比历史均值和行业基准。
    使用场景：需要发现数据中的异常点时调用。
    不要用于：查询原始数据（用sql_query）、查询行业基准（用financial_api）。
    本工具会自动查询数据并进行异常分析。""",
    "parameters": {
        "metric": {
            "type": "string",
            "enum": ["overdue_rate", "activation_rate", "churn_rate",
                     "collection_recovery_rate", "new_customers",
                     "revenue_per_customer", "all"],
            "description": "要检测的指标，'all'表示检测所有指标"
        },
        "period": {
            "type": "string",
            "description": "检测时间范围，如'2026-03'或'recent_3_months'",
            "default": "recent_3_months"
        }
    }
}
```

实现逻辑：

1. 从SQLite查询指定指标的历史数据
2. 计算历史均值和标准差
3. 当前值偏离超过2个标准差 → 标记为异常
4. 对比行业基准，偏离超过阈值 → 标记为异常
5. 输出异常评分（severity: low/medium/high/critical）

### 工具五：report_gen（报告生成）

```python
tool_description = {
    "name": "report_gen",
    "description": """生成结构化分析报告，包含关键发现、异常项、根因分析和行动建议。
    使用场景：Agent已完成数据采集和分析后，生成最终报告时调用。
    必须在其他工具调用完成后使用。""",
    "parameters": {
        "findings": {
            "type": "string",
            "description": "前面步骤收集到的所有发现，JSON格式"
        }
    }
}
```

输出格式（Pydantic模型定义）：

```python
class ActionItem(BaseModel):
    title: str                    # 行动标题
    description: str              # 详细描述
    priority: Literal["P0", "P1", "P2", "P3"]  # 优先级
    expected_impact: str          # 预计影响
    owner_suggestion: str         # 建议负责人
    deadline_suggestion: str      # 建议截止日期

class AnomalyFinding(BaseModel):
    metric: str                   # 异常指标
    region: str                   # 异常区域
    current_value: float          # 当前值
    baseline_value: float         # 基准值
    deviation_pct: float          # 偏离百分比
    severity: Literal["low", "medium", "high", "critical"]
    root_cause_hypothesis: str    # 根因假设

class AnalysisReport(BaseModel):
    report_id: str                # 报告唯一ID
    generated_at: str             # 生成时间
    period: str                   # 分析周期
    executive_summary: str        # 执行摘要（2-3句话）
    key_findings: list[str]       # 关键发现列表
    anomalies: list[AnomalyFinding]  # 异常项
    action_items: list[ActionItem]   # 行动建议
    data_sources: list[str]       # 数据来源
    trace_id: str                 # 追溯ID
    requires_human_review: bool   # 是否需要人工审批
```

### 3.4 Agent Orchestrator 设计

### System Prompt 核心结构

```
<role>
你是FinSight，一个金融数据分析Agent。
你服务于零售银行的业务主管，帮助他们从数据中发现洞察并生成行动建议。
你的核心理念是"从数据到洞察到行动"——不只是展示数字，
而是分析数字背后的含义并给出可执行的建议。
</role>

<tools>
你有5个工具可以使用：
1. sql_query — 查询内部业务数据
2. financial_api — 查询行业基准
3. rag_search — 检索历史案例和最佳实践
4. anomaly_detect — 异常检测和评分
5. report_gen — 生成结构化报告
</tools>

<workflow>
收到用户问题后，遵循以下分析流程：
1. 理解用户意图，确定需要查询哪些数据
2. 调用sql_query获取业务数据
3. 调用financial_api获取行业基准做对比
4. 调用anomaly_detect检测异常
5. 如发现异常，调用rag_search检索历史案例和应对策略
6. 用CoT推理分析根因
7. 调用report_gen生成最终报告
不需要每次都走完所有步骤，根据用户问题灵活调整。
</workflow>

<constraints>
- 所有数字必须来自工具调用，绝不估算或编造
- 如果工具调用失败，告知用户具体原因，不要用编造的数据替代
- 异常严重度为high或critical的发现，报告中标记requires_human_review=true
- 每个发现必须注明数据来源和时间
- 不给出投资建议，只提供数据分析和运营改进建议
</constraints>
```

### ReAct循环实现

```python
async def run_agent(user_input: str):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    for step in range(MAX_STEPS):  # 最多10步，防止死循环
        # 1. 调用LLM
        response = await llm.chat(messages, tools=TOOL_DEFINITIONS)

        # 2. 如果LLM返回文本（无工具调用），结束循环
        if response.is_text():
            yield SSEEvent(type="final", content=response.text)
            break

        # 3. 如果LLM要求调用工具
        if response.is_tool_call():
            tool_name = response.tool_call.name
            tool_args = response.tool_call.arguments

            # 3a. SSE推送当前步骤
            yield SSEEvent(type="step", content=f"正在调用 {tool_name}...")

            # 3b. 执行工具
            try:
                result = await execute_tool(tool_name, tool_args)
            except Exception as e:
                result = f"工具调用失败: {str(e)}"

            # 3c. 将工具结果加入消息历史
            messages.append(response.raw_message)
            messages.append({
                "role": "tool",
                "tool_call_id": response.tool_call.id,
                "content": json.dumps(result, ensure_ascii=False)
            })

            # 3d. 记录Trace
            trace_logger.log_step(step, tool_name, tool_args, result)
```

### 3.5 SSE流式传输设计

```python
# 后端 SSE endpoint
@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    return StreamingResponse(
        agent_stream(request.query),
        media_type="text/event-stream"
    )

async def agent_stream(query: str):
    async for event in run_agent(query):
        yield f"data: {json.dumps(event.dict(), ensure_ascii=False)}\\n\\n"
```

SSE事件类型：

| 事件类型    | 用途                             | 前端处理                   |
| ----------- | -------------------------------- | -------------------------- |
| step        | Agent执行了一步（工具调用/推理） | 追加到推理过程面板         |
| thinking    | Agent的推理过程文本              | 显示在推理面板（灰色斜体） |
| tool_call   | 工具调用名称和参数               | 显示工具名称和参数         |
| tool_result | 工具返回结果摘要                 | 显示结果摘要               |
| report      | 最终报告JSON                     | 渲染到报告面板             |
| error       | 错误信息                         | 显示错误提示               |
| done        | 流结束                           | 关闭SSE连接                |

### 3.6 Trace日志设计（审计可追溯）

```python
class TraceLog(BaseModel):
    trace_id: str           # UUID
    timestamp: str          # ISO格式时间戳
    user_query: str         # 用户原始输入
    steps: list[TraceStep]  # 每步记录
    final_report: dict      # 最终报告
    total_tokens: int       # 总token消耗
    total_latency_ms: int   # 总延迟
    llm_model: str          # 使用的模型
    status: str             # success / error

class TraceStep(BaseModel):
    step_number: int
    action_type: str        # "tool_call" / "llm_reasoning"
    tool_name: str | None
    tool_input: dict | None
    tool_output: str | None
    llm_input_tokens: int
    llm_output_tokens: int
    latency_ms: int
    timestamp: str
```

每次分析完成后，完整TraceLog存入SQLite的traces表。

------

## 四、前端设计

### 4.1 页面布局

```
┌──────────────────────────────────────────────────────┐
│  FinSight Agent              [Model: GPT-4o ▾] [⚙]  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │           KPI指标概览卡片（横向排列）              │ │
│  │  获客量    激活率    交易额    逾期率    催收率    │ │
│  │  12,450   78.3%    8,230万   3.8%    85.2%     │ │
│  │  ↑5.2%    ↓1.1%   ↑3.4%    ↑0.6%   ↓2.1%    │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─────────────────────┐  ┌──────────────────────┐  │
│  │                     │  │                      │  │
│  │   Agent 推理过程     │  │   分析报告            │  │
│  │                     │  │                      │  │
│  │  🔍 正在查询业务数据  │  │   执行摘要            │  │
│  │  ✅ 获取到60条记录   │  │   ──────────         │  │
│  │  🔍 正在检测异常     │  │   关键发现            │  │
│  │  ⚠️ 发现2个异常     │  │   • 华东区逾期率...   │  │
│  │  🔍 检索历史案例     │  │                      │  │
│  │  💡 分析根因...      │  │   异常项              │  │
│  │  📝 生成报告         │  │   🔴 华东区逾期率     │  │
│  │                     │  │   🟡 华南区获客量     │  │
│  │                     │  │                      │  │
│  │                     │  │   行动建议            │  │
│  │                     │  │   P0: 收紧华东审批    │  │
│  │                     │  │   P1: 华南获客调研    │  │
│  │                     │  │                      │  │
│  │                     │  │  [✅ Approve] [❌ Reject]│
│  └─────────────────────┘  └──────────────────────┘  │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  💬 请输入分析需求...                    [发送]  │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### 4.2 前端组件结构

```
src/
├── App.tsx                    # 主应用
├── components/
│   ├── KPICards.tsx           # 顶部指标卡片
│   ├── ChatInput.tsx          # 底部输入框
│   ├── ReasoningPanel.tsx     # 左侧推理过程
│   ├── ReportPanel.tsx        # 右侧报告展示
│   ├── AnomalyCard.tsx        # 异常项卡片
│   ├── ActionItemCard.tsx     # 行动建议卡片
│   ├── ApprovalButtons.tsx    # 审批按钮
│   └── ModelSelector.tsx      # LLM模型切换
├── hooks/
│   ├── useSSE.ts              # SSE连接管理
│   └── useAgent.ts            # Agent状态管理
├── types/
│   └── index.ts               # TypeScript类型定义
└── utils/
    └── api.ts                 # API调用封装
```

------

## 五、项目目录结构

```
finsight-agent/
├── README.md                  # 项目说明 + 架构图 + 启动方式
├── DESIGN.md                  # 本文档
├── docker-compose.yml         # 一键部署
├── .env.example               # 环境变量模板
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                # FastAPI入口
│   ├── config.py              # 配置管理
│   │
│   ├── agent/
│   │   ├── orchestrator.py    # Agent编排器（ReAct循环）
│   │   ├── prompts.py         # System Prompt + 工具描述
│   │   └── models.py          # Pydantic数据模型
│   │
│   ├── tools/
│   │   ├── registry.py        # 工具注册表
│   │   ├── sql_query.py       # Text-to-SQL工具
│   │   ├── financial_api.py   # 行业基准查询
│   │   ├── rag_search.py      # RAG检索
│   │   ├── anomaly_detect.py  # 异常检测
│   │   └── report_gen.py      # 报告生成
│   │
│   ├── llm/
│   │   └── provider.py        # 多LLM Provider统一接口
│   │
│   ├── knowledge_base/
│   │   ├── metadata.json      # 字段元数据
│   │   ├── business_rules.json# 业务规则
│   │   ├── cases/             # 历史案例markdown文件
│   │   └── indexer.py         # 知识库向量化脚本
│   │
│   ├── db/
│   │   ├── init_db.py         # 数据库初始化 + 模拟数据生成
│   │   └── finsight.db        # SQLite数据库（git忽略）
│   │
│   └── trace/
│       └── logger.py          # Trace日志记录
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── public/
│   └── src/
│       ├── App.tsx
│       ├── components/        # 见4.2组件结构
│       ├── hooks/
│       ├── types/
│       └── utils/
│
└── scripts/
    ├── seed_data.py           # 生成模拟数据
    └── index_knowledge_base.py# 向量化知识库
```

------

## 六、部署方案

### 6.1 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
python db/init_db.py              # 初始化数据库 + 生成模拟数据
python knowledge_base/indexer.py  # 向量化知识库
uvicorn main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev                       # 默认 <http://localhost:5173>
```

### 6.2 Docker Compose 本地验证

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LLM_PROVIDER=${LLM_PROVIDER:-openai}
      - LLM_MODEL=${LLM_MODEL:-gpt-4o}
    volumes:
      - ./data:/app/data          # 持久化数据库和向量库

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
# 一键启动
cp .env.example .env
# 编辑.env填入API Key
docker compose up -d
# 访问 <http://localhost:3000>
```

### 6.3 服务器部署（国内云服务器）

```
推荐配置：阿里云/腾讯云轻量应用服务器
  CPU: 2核
  内存: 4GB
  硬盘: 50GB SSD
  带宽: 5Mbps
  系统: Ubuntu 22.04
  费用: 约50-100元/月
```

部署步骤：

```bash
# 1. 安装Docker
curl -fsSL <https://get.docker.com> | sh

# 2. 克隆代码
git clone <https://github.com/yourname/finsight-agent.git>
cd finsight-agent

# 3. 配置环境变量
cp .env.example .env
vim .env  # 填入API Key

# 4. 一键部署
docker compose up -d

# 5. 配置Nginx反向代理（可选，如需域名）
# 或者直接用 <http://服务器IP:3000> 访问
```

### 6.4 备选：办公室机器 + 穿透

```bash
# 办公室机器上启动服务
docker compose up -d

# nps穿透配置
# 在nps服务端配置TCP隧道
# 将办公室的8000端口和3000端口映射到公网
# 用户通过公网地址访问
```

------

## 七、开发节奏

| 天数  | 任务                                                         | 交付物                |
| ----- | ------------------------------------------------------------ | --------------------- |
| Day 1 | 搭骨架：FastAPI + React脚手架、LLM Provider层、基本ReAct循环跑通、生成模拟数据 | 能输入问题得到LLM回复 |
| Day 2 | 核心工具：sql_query（Text-to-SQL）+ anomaly_detect（异常检测） | 能查数据、能检测异常  |
| Day 3 | RAG模块：知识库构建 + Chroma向量化 + rag_search工具 + financial_api工具 | 能检索案例、能查基准  |
| Day 4 | 串联：完整Agent流程跑通 + report_gen + SSE流式输出           | 端到端流程完整        |
| Day 5 | 前端打磨：KPI卡片 + 推理面板 + 报告面板 + 审批按钮 + Trace日志 | 界面可演示            |
| Day 6 | Docker化 + 部署 + README + 整体测试                          | 可在线访问            |

------

## 八、项目展示要点

### 8.1 开场（30秒）

"这是一个金融数据智能分析 Agent：用户自然语言提问，Agent 自动从多数据源采集、异常检测、根因推理、生成优先级排序的行动建议。核心理念是'从数据到洞察到行动'——不只是查数据，而是自动发现异常、分析根因、给出可执行建议。"

### 8.2 现场演示流程

1. 打开页面，展示KPI概览
2. 输入"信用卡业务上个月有什么异常？"
3. 实时展示Agent推理过程（SSE流）
4. 展示最终报告——异常项（华东逾期率）、根因分析、行动建议
5. 点击Approve按钮，展示Human-in-the-Loop
6. 切换LLM Provider（从OpenAI切到DeepSeek），展示多后端能力

### 8.3 架构追问 FAQ

常见的技术追问和回答方向：

| 追问                        | 回答方向                                            |
| --------------------------- | --------------------------------------------------- |
| Text-to-SQL准确率怎么保证？ | 元数据知识库 + RAG动态注入 + SQL执行报错自动重试    |
| 为什么不直接用LangChain？   | 控制力和可审计性，金融场景需要Harness层完全可控     |
| 异常检测用什么方法？        | 统计方法（均值+标准差）+ 行业基准对比，不过度工程化 |
| 怎么防止LLM编造数据？       | 所有数字必须来自工具调用，prompt硬约束 + 输出验证   |
| 生产中怎么扩展？            | Chroma→Milvus，SQLite→PostgreSQL，加Redis缓存       |
| 怎么处理多轮对话？          | 消息历史管理 + 上下文窗口截断策略                   |