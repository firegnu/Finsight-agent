"""Tool registry — add new tools by appending to the two dicts below."""
from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable

from . import (
    anomaly_detect,
    financial_api,
    rag_search,
    report_gen,
    sql_query,
    use_skill,
)


ToolHandler = Callable[..., Awaitable[dict]]


TOOL_DEFINITIONS: list[dict] = [
    use_skill.TOOL_SCHEMA,
    sql_query.TOOL_SCHEMA,
    anomaly_detect.TOOL_SCHEMA,
    financial_api.TOOL_SCHEMA,
    rag_search.TOOL_SCHEMA,
    report_gen.TOOL_SCHEMA,
]


TOOL_HANDLERS: dict[str, ToolHandler] = {
    "use_skill": use_skill.run,
    "sql_query": sql_query.run,
    "anomaly_detect": anomaly_detect.run,
    "financial_api": financial_api.run,
    "rag_search": rag_search.run,
    "report_gen": report_gen.run,
}


async def execute_tool(
    name: str, args: dict[str, Any], provider_id: str | None = None
) -> dict:
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return {"error": f"Unknown tool: {name}"}
    # Forward provider_id only to handlers that declare it (sql_query,
    # report_gen). Tools that don't hit an LLM (anomaly_detect, rag_search,
    # use_skill, financial_api) ignore it.
    call_args = dict(args)
    sig = inspect.signature(handler)
    if "provider_id" in sig.parameters and "provider_id" not in call_args:
        call_args["provider_id"] = provider_id
    try:
        return await handler(**call_args)
    except TypeError as e:
        return {"error": f"Invalid args for {name}: {e}"}
    except Exception as e:  # noqa: BLE001
        return {"error": f"Tool {name} raised: {type(e).__name__}: {e}"}
