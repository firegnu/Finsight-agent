"""Real-time KPI aggregation from credit_card_metrics + industry_benchmark.

Replaces the hardcoded /api/kpi response with live SQLite aggregation:
- 获客量：SUM(new_customers) across regions
- 交易额：SUM(monthly_transaction_volume) across regions
- Rates (激活率/逾期率/催收回收率)：weighted average (weight by transaction volume)
- change%：relative delta vs previous month
- alert：true if aggregated value breaches industry_benchmark threshold
"""
from __future__ import annotations

from .database import query_all


KPI_CONFIG = [
    # Display name, metric column, agg method, unit formatter
    ("获客量",       "new_customers",              "sum",        "count"),
    ("激活率",       "activation_rate",            "weighted",   "percent"),
    ("交易额",       "monthly_transaction_volume", "sum",        "wanyuan"),
    ("逾期率",       "overdue_rate",               "weighted",   "percent"),
    ("催收回收率",    "collection_recovery_rate",   "weighted",   "percent"),
]

# Weight column for weighted averages
_WEIGHT_COL = "monthly_transaction_volume"


def _latest_two_months() -> tuple[str, str | None]:
    rows = query_all(
        "SELECT DISTINCT year_month FROM credit_card_metrics ORDER BY year_month DESC LIMIT 2"
    )
    if not rows:
        return ("", None)
    if len(rows) == 1:
        return (rows[0]["year_month"], None)
    return (rows[0]["year_month"], rows[1]["year_month"])


def _aggregate_for_month(metric: str, agg: str, year_month: str) -> float | None:
    if agg == "sum":
        rows = query_all(
            f"SELECT SUM({metric}) AS v FROM credit_card_metrics WHERE year_month = ?",
            (year_month,),
        )
        v = rows[0]["v"]
        return float(v) if v is not None else None
    if agg == "weighted":
        rows = query_all(
            f"SELECT SUM({metric} * {_WEIGHT_COL}) / SUM({_WEIGHT_COL}) AS v "
            f"FROM credit_card_metrics WHERE year_month = ?",
            (year_month,),
        )
        v = rows[0]["v"]
        return float(v) if v is not None else None
    raise ValueError(f"unknown agg: {agg}")


def _load_benchmark_map() -> dict:
    rows = query_all(
        "SELECT metric_name, benchmark_value, direction FROM industry_benchmark"
    )
    return {r["metric_name"]: r for r in rows}


def _format_value(value: float, unit: str) -> str:
    if unit == "percent":
        return f"{value * 100:.1f}%"
    if unit == "wanyuan":
        return f"{value:,.0f}万"
    if unit == "count":
        return f"{int(round(value)):,}"
    return str(value)


def _change_label(current: float, prev: float | None) -> tuple[str, str]:
    """Return (change_label, trend). trend ∈ {up, down, flat}."""
    if prev is None or prev == 0:
        return ("—", "flat")
    delta = current - prev
    pct = delta / prev * 100
    if abs(pct) < 0.05:
        return ("±0.0%", "flat")
    sign = "+" if delta > 0 else "-"
    return (f"{sign}{abs(pct):.1f}%", "up" if delta > 0 else "down")


def _is_alert(metric: str, value: float, benchmark_row: dict | None) -> bool:
    """Alert when aggregated value breaches the industry benchmark in the
    bad direction (>=10% worse than benchmark)."""
    if not benchmark_row:
        return False
    bm = benchmark_row["benchmark_value"]
    direction = benchmark_row["direction"]
    if direction == "lower_is_better":
        # Bad if current materially above benchmark (>10% worse)
        return value > bm * 1.10
    if direction == "higher_is_better":
        # Bad if current materially below benchmark (<10% worse)
        return value < bm * 0.90
    return False


def aggregate_kpi() -> dict:
    """Build the /api/kpi response from live DB data."""
    latest, prev = _latest_two_months()
    if not latest:
        return {
            "period": "",
            "updated_at": "",
            "metrics": [],
            "error": "no data in credit_card_metrics — run scripts/seed_data.py",
        }

    benchmarks = _load_benchmark_map()
    metrics: list[dict] = []

    for name, col, agg, unit in KPI_CONFIG:
        current = _aggregate_for_month(col, agg, latest)
        previous = _aggregate_for_month(col, agg, prev) if prev else None
        if current is None:
            continue
        change_label, trend = _change_label(current, previous)
        alert = _is_alert(col, current, benchmarks.get(col))
        metrics.append({
            "name": name,
            "metric_name": col,
            "value": _format_value(current, unit),
            "change": change_label,
            "trend": trend,
            "alert": alert,
        })

    # Reuse the latest month's generated_at as the snapshot timestamp
    return {
        "period": latest,
        "prev_period": prev or "",
        "updated_at": f"{latest}-01T00:00:00Z",
        "metrics": metrics,
    }
