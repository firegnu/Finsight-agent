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
MAX_TOOL_PAYLOAD_CHARS = 20000


def _summarize_tool_result(name: str, result: dict) -> str:
    if "error" in result:
        return f"❌ {str(result['error'])[:200]}"
    if name == "sql_query":
        return f"✅ 执行 SQL，返回 {result.get('row_count', 0)} 行"
    if name == "anomaly_detect":
        return f"✅ 检测完成，发现 {result.get('anomaly_count', 0)} 个异常"
    if name == "report_gen":
        return (
            f"✅ 报告生成完成（{len(result.get('anomalies', []))} 异常 / "
            f"{len(result.get('action_items', []))} 建议）"
        )
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

    completed = False
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
        except Exception as e:  # noqa: BLE001
            logger.exception("LLM call failed at step %d", step)
            yield SSEEvent(type="error", data={"msg": f"LLM call failed: {e}"})
            trace.status = "error"
            completed = True
            break

        msg = response.choices[0].message

        if msg.content:
            yield SSEEvent(type="thinking", data={"content": msg.content, "step": step})
            trace.steps.append(TraceStep(
                step_number=step,
                action_type="llm_reasoning",
                tool_output_summary=msg.content[:MAX_TOOL_RESULT_SUMMARY],
                latency_ms=int((time.time() - step_t) * 1000),
            ))

        if not msg.tool_calls:
            yield SSEEvent(type="final_text", data={"content": msg.content or ""})
            trace.status = "success"
            completed = True
            break

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
        })

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
                    "name": tool_name, "error": str(result["error"]), "step": step,
                })
            else:
                yield SSEEvent(type="tool_result", data={
                    "name": tool_name,
                    "summary": _summarize_tool_result(tool_name, result),
                    "step": step,
                })

            trace.steps.append(TraceStep(
                step_number=step,
                action_type="tool_call",
                tool_name=tool_name,
                tool_input=tool_args,
                tool_output_summary=_summarize_tool_result(tool_name, result),
                latency_ms=int((time.time() - tool_t) * 1000),
            ))

            payload = json.dumps(result, ensure_ascii=False, default=str)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": payload[:MAX_TOOL_PAYLOAD_CHARS],
            })

            if tool_name == "report_gen" and "error" not in result:
                report_result = result

        if report_result is not None:
            yield SSEEvent(type="report", data=report_result)
            trace.status = "success"
            completed = True
            break

    if not completed:
        yield SSEEvent(type="error", data={
            "msg": f"Reached max steps ({settings.max_agent_steps})",
        })
        trace.status = "error"

    trace.total_latency_ms = int((time.time() - t_start) * 1000)
    yield SSEEvent(type="done", data={
        "trace_id": trace.trace_id,
        "total_latency_ms": trace.total_latency_ms,
        "status": trace.status,
    })
