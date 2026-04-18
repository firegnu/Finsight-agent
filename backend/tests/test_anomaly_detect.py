import asyncio

import pytest

from backend.tools.anomaly_detect import compute_anomaly, run


def test_no_anomaly_within_2_sigma():
    result = compute_anomaly(current=3.3, mean=3.2, std=0.2)
    assert result["severity"] == "low"
    assert result["is_anomaly"] is False


def test_medium_anomaly_just_above_2_sigma():
    # 2.25σ
    result = compute_anomaly(current=3.65, mean=3.2, std=0.2)
    assert result["severity"] == "medium"
    assert result["is_anomaly"] is True


def test_high_anomaly_above_2_5_sigma():
    # 2.75σ
    result = compute_anomaly(current=3.75, mean=3.2, std=0.2)
    assert result["severity"] == "high"
    assert result["is_anomaly"] is True


def test_critical_anomaly_above_3_sigma():
    # 13σ
    result = compute_anomaly(current=5.8, mean=3.2, std=0.2)
    assert result["severity"] == "critical"
    assert result["is_anomaly"] is True


def test_zero_std_handled():
    result = compute_anomaly(current=3.2, mean=3.2, std=0.0)
    assert result["is_anomaly"] is False


def test_detects_east_march_overdue():
    """集成测试：真实跑 run() 应该发现华东 2026-03 逾期率 critical 异常."""
    result = asyncio.run(run("overdue_rate", "2026-03"))
    assert result["anomaly_count"] >= 1
    east_march = [
        f for f in result["findings"]
        if f["region"] == "华东" and f["period"] == "2026-03" and f["metric"] == "overdue_rate"
    ]
    assert len(east_march) == 1
    assert east_march[0]["severity"] == "critical"


def test_detects_south_new_customers_drop():
    result = asyncio.run(run("new_customers", "recent_3_months"))
    south = [
        f for f in result["findings"]
        if f["region"] == "华南" and f["metric"] == "new_customers"
    ]
    assert len(south) >= 1
    assert south[0]["severity"] in ("high", "critical")
