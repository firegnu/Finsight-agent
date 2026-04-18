"""ReAct loop with SSE event streaming."""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, AsyncGenerator
from uuid import uuid4

from pydantic import ValidationError

from ..config import settings
from ..db.traces import save_trace
from ..llm.client import MODEL, chat
from ..sse.events import SSEEvent
from ..tools.registry import TOOL_DEFINITIONS, execute_tool
from .models import AnalysisReport, TraceLog, TraceStep
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
    if name == "rag_search":
        hits = result.get("hits", [])
        if not hits:
            return "✅ 检索完成，未找到相关案例"
        titles = "、".join(h.get("title", h.get("id", "?")) for h in hits)
        return f"✅ 命中 {len(hits)} 个案例：{titles}"
    if name == "use_skill":
        skill_name = result.get("name", "?")
        category = result.get("category", "")
        return f"✅ 已加载 skill: {skill_name} ({category})"
    return f"✅ {str(result)[:MAX_TOOL_RESULT_SUMMARY]}"


async def run_agent(user_query: str) -> AsyncGenerator[SSEEvent, None]:
    trace = TraceLog(
        trace_id=f"trace-{uuid4().hex[:12]}",
        user_query=user_query,
        llm_model=MODEL,
    )
    t_start = time.time()
    started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]

    yield SSEEvent(type="start", data={"trace_id": trace.trace_id, "query": user_query})

    completed = False
    for step in range(settings.max_agent_steps):
        step_t = time.time()
        try:
            response = await chat(
                model=MODEL,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=4096,
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
                event_data: dict[str, Any] = {
                    "name": tool_name,
                    "summary": _summarize_tool_result(tool_name, result),
                    "step": step,
                }
                # For rag_search, also attach the hits so the UI can render
                # clickable case cards inline (instead of dumping raw JSON).
                if tool_name == "rag_search" and "hits" in result:
                    event_data["hits"] = result["hits"]
                # For use_skill, attach skill metadata so the UI can render a
                # clickable skill badge (content goes to the Agent's context
                # but frontend only needs name/description for the inline card).
                if tool_name == "use_skill" and "error" not in result:
                    event_data["skill"] = {
                        "name": result.get("name"),
                        "description": result.get("description", ""),
                        "category": result.get("category", ""),
                    }
                yield SSEEvent(type="tool_result", data=event_data)

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
            try:
                trace.final_report = AnalysisReport(**report_result)
            except (ValidationError, TypeError) as e:
                logger.warning("failed to attach final_report to trace: %s", e)
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

    # Persist the full trace to SQLite after the SSE stream is done. Failure
    # here should not break the user-visible response — log and move on.
    try:
        save_trace(trace, started_at=started_at)
    except Exception as e:  # noqa: BLE001
        logger.exception("failed to persist trace %s: %s", trace.trace_id, e)
