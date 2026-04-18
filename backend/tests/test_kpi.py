from backend.db.kpi import aggregate_kpi


def test_aggregate_kpi_shape():
    r = aggregate_kpi()
    assert "error" not in r
    assert r["period"] == "2026-03"
    assert r["prev_period"] == "2026-02"
    assert len(r["metrics"]) == 5
    names = {m["name"] for m in r["metrics"]}
    assert names == {"获客量", "激活率", "交易额", "逾期率", "催收回收率"}


def test_kpi_values_reasonable():
    r = aggregate_kpi()
    kpi_by_name = {m["name"]: m for m in r["metrics"]}

    # 获客量 should be sum across 5 regions, formatted with commas
    acquisition = kpi_by_name["获客量"]
    assert "," in acquisition["value"] or acquisition["value"].isdigit()

    # 激活率 should be percentage, roughly 70-85%
    activation = kpi_by_name["激活率"]["value"]
    assert activation.endswith("%")
    act_num = float(activation.rstrip("%"))
    assert 60 < act_num < 90

    # 逾期率 should be percentage
    overdue = kpi_by_name["逾期率"]["value"]
    assert overdue.endswith("%")


def test_overdue_triggers_alert():
    """With synthetic data (华东 2026-03 overdue at 5.8%), aggregated overdue
    should be pulled well above the 3.5% benchmark → alert=True."""
    r = aggregate_kpi()
    overdue = next(m for m in r["metrics"] if m["name"] == "逾期率")
    # The engineered east spike dominates the weighted avg enough to breach benchmark+10%
    assert overdue["alert"] is True


def test_change_vs_prev_month_present():
    r = aggregate_kpi()
    for m in r["metrics"]:
        assert m["change"]  # non-empty string
        assert m["trend"] in ("up", "down", "flat")
