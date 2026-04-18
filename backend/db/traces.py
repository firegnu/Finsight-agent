"""Trace log persistence — writes TraceLog to SQLite after each Agent run."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from ..agent.models import TraceLog
from .database import get_connection, query_all, query_one


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def save_trace(trace: TraceLog, started_at: str | None = None) -> None:
    """Persist a TraceLog + all its steps in a single transaction."""
    completed_at = _utc_iso() if trace.status != "running" else None
    final_report_json = (
        json.dumps(trace.final_report.model_dump(), ensure_ascii=False)
        if trace.final_report
        else None
    )

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO traces "
            "(trace_id, user_query, llm_model, status, total_latency_ms, "
            " step_count, started_at, completed_at, final_report_json) "
            "VALUES (?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(trace_id) DO UPDATE SET "
            "  user_query = excluded.user_query, "
            "  llm_model = excluded.llm_model, "
            "  status = excluded.status, "
            "  total_latency_ms = excluded.total_latency_ms, "
            "  step_count = excluded.step_count, "
            "  completed_at = excluded.completed_at, "
            "  final_report_json = excluded.final_report_json",
            (
                trace.trace_id,
                trace.user_query,
                trace.llm_model,
                trace.status,
                trace.total_latency_ms,
                len(trace.steps),
                started_at or _utc_iso(),
                completed_at,
                final_report_json,
            ),
        )
        # Replace all existing steps for idempotency
        conn.execute("DELETE FROM trace_steps WHERE trace_id = ?", (trace.trace_id,))
        if trace.steps:
            conn.executemany(
                "INSERT INTO trace_steps "
                "(trace_id, step_number, action_type, tool_name, "
                " tool_input_json, tool_output_summary, latency_ms, timestamp) "
                "VALUES (?,?,?,?,?,?,?,?)",
                [
                    (
                        trace.trace_id,
                        s.step_number,
                        s.action_type,
                        s.tool_name,
                        json.dumps(s.tool_input, ensure_ascii=False) if s.tool_input else None,
                        s.tool_output_summary,
                        s.latency_ms,
                        s.timestamp,
                    )
                    for s in trace.steps
                ],
            )
        conn.commit()


def list_traces(limit: int = 50) -> list[dict]:
    rows = query_all(
        "SELECT trace_id, user_query, llm_model, status, total_latency_ms, "
        "       step_count, started_at, completed_at "
        "FROM traces ORDER BY started_at DESC LIMIT ?",
        (limit,),
    )
    return rows


def get_trace_detail(trace_id: str) -> dict | None:
    trace = query_one(
        "SELECT trace_id, user_query, llm_model, status, total_latency_ms, "
        "       step_count, started_at, completed_at, final_report_json "
        "FROM traces WHERE trace_id = ?",
        (trace_id,),
    )
    if not trace:
        return None

    steps = query_all(
        "SELECT step_number, action_type, tool_name, tool_input_json, "
        "       tool_output_summary, latency_ms, timestamp "
        "FROM trace_steps WHERE trace_id = ? ORDER BY step_number, id",
        (trace_id,),
    )
    # Parse JSON fields for client convenience
    parsed_steps = []
    for s in steps:
        tool_input_raw = s.pop("tool_input_json", None)
        s["tool_input"] = json.loads(tool_input_raw) if tool_input_raw else None
        parsed_steps.append(s)
    trace["steps"] = parsed_steps

    report_raw = trace.pop("final_report_json", None)
    trace["final_report"] = json.loads(report_raw) if report_raw else None

    return trace


def delete_trace(trace_id: str) -> bool:
    """Remove a trace + its steps. Returns True if a record was deleted."""
    existing = query_one("SELECT id FROM traces WHERE trace_id = ?", (trace_id,))
    if not existing:
        return False
    with get_connection() as conn:
        conn.execute("DELETE FROM trace_steps WHERE trace_id = ?", (trace_id,))
        conn.execute("DELETE FROM traces WHERE trace_id = ?", (trace_id,))
        conn.commit()
    return True
