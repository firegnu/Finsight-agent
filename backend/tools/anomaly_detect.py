"""Statistical anomaly detection over historical mean ± std."""
from __future__ import annotations

import logging
import re
import statistics

from ..db.database import query_all

logger = logging.getLogger("finsight.anomaly_detect")


METRICS_ENUM = [
    "overdue_rate",
    "activation_rate",
    "churn_rate",
    "collection_recovery_rate",
    "new_customers",
    "revenue_per_customer",
    "monthly_transaction_volume",
    "customer_complaints",
    "all",
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
    """Return (start_month, end_month) inclusive. None for unknown period."""
    if re.match(r"^\d{4}-\d{2}$", period):
        return (period, period)
    if period == "recent_3_months":
        return ("2026-01", "2026-03")
    if period == "recent_6_months":
        return ("2025-10", "2026-03")
    return None


def _detect_for_metric(metric: str, start: str, end: str) -> list[dict]:
    rows = query_all(
        f"SELECT region, year_month, {metric} AS value "
        f"FROM credit_card_metrics ORDER BY region, year_month"
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
        if m not in _METRICS_ALL:
            return {"error": f"Unknown metric: {m}"}
        all_findings.extend(_detect_for_metric(m, start, end))

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_findings.sort(key=lambda f: (severity_rank[f["severity"]], -f["deviation_sigma"]))

    logger.info(
        "anomaly_detect found %d anomalies for metric=%s period=%s",
        len(all_findings), metric, period,
    )
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
                "metric": {
                    "type": "string",
                    "enum": METRICS_ENUM,
                    "description": "要检测的指标，'all' 表示全部",
                },
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
