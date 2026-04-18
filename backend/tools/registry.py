"""Tool registry — add new tools by appending to the two dicts below.

Week 2 additions will simply add entries here without touching the orchestrator.
"""
from typing import Any, Awaitable, Callable

from . import (
    anomaly_detect,
    financial_api,
    rag_search,
    report_gen,
    sql_query,
)


ToolHandler = Callable[..., Awaitable[dict]]


TOOL_DEFINITIONS: list[dict] = [
    sql_query.TOOL_SCHEMA,
    anomaly_detect.TOOL_SCHEMA,
    financial_api.TOOL_SCHEMA,
    rag_search.TOOL_SCHEMA,
    report_gen.TOOL_SCHEMA,
]


TOOL_HANDLERS: dict[str, ToolHandler] = {
    "sql_query": sql_query.run,
    "anomaly_detect": anomaly_detect.run,
    "financial_api": financial_api.run,
    "rag_search": rag_search.run,
    "report_gen": report_gen.run,
}


async def execute_tool(name: str, args: dict[str, Any]) -> dict:
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return {"error": f"Unknown tool: {name}"}
    try:
        return await handler(**args)
    except TypeError as e:
        return {"error": f"Invalid args for {name}: {e}"}
    except Exception as e:  # noqa: BLE001
        return {"error": f"Tool {name} raised: {type(e).__name__}: {e}"}
