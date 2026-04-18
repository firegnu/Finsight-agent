"""financial_api tool — industry benchmark lookup.

Wraps SQLite-backed industry_benchmark table. For an MVP demo, this plays
the role of a generic 'financial data provider' abstraction; in production
this could dispatch to Daloopa / FactSet / S&P / internal benchmark APIs.
"""
from __future__ import annotations

import logging

from ..db.database import query_all

logger = logging.getLogger("finsight.financial_api")


VALID_METRICS = [
    "overdue_rate",
    "activation_rate",
    "churn_rate",
    "collection_recovery_rate",
    "new_customers",
    "revenue_per_customer",
    "monthly_transaction_volume",
    "customer_complaints",
]


async def run(metric_name: str) -> dict:
    """Return industry benchmark for a metric."""
    if metric_name not in VALID_METRICS:
        return {
            "error": f"unknown metric '{metric_name}'. valid: {', '.join(VALID_METRICS)}",
        }

    rows = query_all(
        "SELECT metric_name, metric_cn, benchmark_value, direction, unit, source, "
        "updated_at, description FROM industry_benchmark WHERE metric_name = ?",
        (metric_name,),
    )
    if not rows:
        return {"error": f"no benchmark found for metric '{metric_name}'"}

    row = rows[0]
    logger.info("financial_api hit: %s = %s (%s)", metric_name, row["benchmark_value"], row["source"])
    return {
        "metric": row["metric_name"],
        "metric_cn": row["metric_cn"],
        "benchmark_value": row["benchmark_value"],
        "direction": row["direction"],  # "lower_is_better" | "higher_is_better"
        "unit": row["unit"],
        "source": row["source"],
        "updated_at": row["updated_at"],
        "description": row["description"],
    }


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "financial_api",
        "description": (
            "查询金融行业基准数据（用于本司指标对标）。"
            "使用场景：发现异常后，需要对比本司值与行业基准，判断严重度和偏离方向。"
            "不要用于查询本司内部数据（用 sql_query 或 anomaly_detect）。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "metric_name": {
                    "type": "string",
                    "enum": VALID_METRICS,
                    "description": "要查询的指标英文字段名",
                },
            },
            "required": ["metric_name"],
        },
    },
}
