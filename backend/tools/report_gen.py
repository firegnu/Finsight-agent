"""Structured report generator using Pydantic schema + JSON mode."""
from __future__ import annotations

import json
import logging
from uuid import uuid4

from pydantic import ValidationError

from ..agent.models import AnalysisReport
from ..llm.client import MODEL, chat

logger = logging.getLogger("finsight.report_gen")

MAX_RETRIES = 2


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
      "root_cause_hypothesis": "string，基于数据、历史案例和业务常识的根因推测",
      "references": ["string，RAG 检索到的历史案例 id，如 'east-2024-q3-overdue-spike'；无则空数组"]
    }
  ],
  "action_items": [
    {
      "title": "string，简洁",
      "description": "string，具体可执行",
      "priority": "P0 | P1 | P2 | P3",
      "expected_impact": "string",
      "owner_suggestion": "string，如 '风控部负责人'",
      "deadline_suggestion": "string，如 '7 天内' 或 '2026-04-30'"
    }
  ],
  "data_sources": ["string，如 'credit_card_metrics 表 2025-04~2026-03'"],
  "requires_human_review": true
}

规则：
- severity 为 high/critical 时，requires_human_review=true
- 每个异常至少配一个行动建议
- 只输出 JSON，不要任何解释、不要 markdown 代码块
- 数字字段保持原始精度
- baseline_value 字段本次保持 null（待 financial_api 工具上线后填充）
- references 字段：如 findings_summary 里带了历史案例 id（RAG 检索结果），在对应 anomaly
  下填入；根因推测也要结合这些案例的经验，在 root_cause_hypothesis 里体现"历史上类似情况..."
"""


def _strip_code_fence(raw: str) -> str:
    import re
    s = raw.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```\s*$", "", s)
    return s.strip()


async def run(findings_summary: str) -> dict:
    """Generate structured report from prior findings."""
    last_err: str | None = None
    last_raw: str | None = None

    for attempt in range(MAX_RETRIES + 1):
        user_msg = f"分析发现：\n{findings_summary}"
        if last_err:
            user_msg += f"\n\n上次生成的 JSON 有错误：{last_err}\n请修正后重新生成。"

        response = await chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": REPORT_SYS_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=8192,
        )
        last_raw = response.choices[0].message.content or "{}"
        try:
            parsed = json.loads(_strip_code_fence(last_raw))
            parsed.setdefault("report_id", f"rpt-{uuid4().hex[:8]}")
            parsed.setdefault("trace_id", f"trace-{uuid4().hex[:12]}")
            report = AnalysisReport(**parsed)
            logger.info("report_gen success on attempt %d", attempt + 1)
            return report.model_dump()
        except (json.JSONDecodeError, ValidationError) as e:
            last_err = f"{type(e).__name__}: {str(e)[:2000]}"
            logger.warning("report_gen attempt %d failed: %s", attempt + 1, last_err)

    return {
        "error": f"report_gen failed after {MAX_RETRIES + 1} attempts: {last_err}",
        "raw_output": last_raw,
    }


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
