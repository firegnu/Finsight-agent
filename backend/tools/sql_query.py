"""Text-to-SQL tool with safety validator + retry."""
from __future__ import annotations

import logging
import re

from ..agent.prompts import SQL_GEN_PROMPT
from ..db.database import query_all
from ..llm.client import llm, MODEL

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
    stripped = sql.strip().rstrip(";").strip()
    if ";" in stripped:
        raise SQLValidationError("Multiple statements not allowed")
    if not re.match(r"^\s*SELECT\b", stripped, re.IGNORECASE):
        raise SQLValidationError(f"Only SELECT statements allowed, got: {stripped[:80]}")
    if FORBIDDEN.search(stripped):
        raise SQLValidationError(f"Forbidden keyword detected in: {stripped[:80]}")


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
    sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\s*```\s*$", "", sql)
    return sql.strip().rstrip(";")


async def run(query_description: str) -> dict:
    """Tool entry point: natural-language description → SQL → rows."""
    last_err: str | None = None
    last_sql: str | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            last_sql = await generate_sql(query_description, prior_error=last_err)
            validate_sql_readonly(last_sql)
            rows = query_all(last_sql)
            truncated = len(rows) > MAX_ROWS_RETURNED
            if truncated:
                rows = rows[:MAX_ROWS_RETURNED]
            logger.info("sql_query success on attempt %d: %s", attempt + 1, last_sql)
            return {
                "sql": last_sql,
                "row_count": len(rows),
                "truncated": truncated,
                "rows": rows,
            }
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            logger.warning("sql_query attempt %d failed: %s", attempt + 1, last_err)
    return {"error": last_err or "unknown", "sql_attempted": last_sql}


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
