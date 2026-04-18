import asyncio

from backend.tools.financial_api import run


def test_returns_benchmark_for_overdue_rate():
    result = asyncio.run(run("overdue_rate"))
    assert "error" not in result
    assert result["metric"] == "overdue_rate"
    assert result["metric_cn"] == "逾期率"
    assert result["direction"] == "lower_is_better"
    assert 0 < result["benchmark_value"] < 1
    assert result["source"]


def test_returns_benchmark_for_activation_rate():
    result = asyncio.run(run("activation_rate"))
    assert result["direction"] == "higher_is_better"
    assert result["metric_cn"] == "激活率"


def test_unknown_metric_returns_error():
    result = asyncio.run(run("nonexistent"))
    assert "error" in result
    assert "unknown" in result["error"].lower()


def test_all_valid_metrics_resolve():
    """Ensure every metric declared in the tool enum has a benchmark row."""
    from backend.tools.financial_api import VALID_METRICS

    for m in VALID_METRICS:
        result = asyncio.run(run(m))
        assert "error" not in result, f"metric '{m}' has no benchmark row"
        assert result["benchmark_value"] > 0
