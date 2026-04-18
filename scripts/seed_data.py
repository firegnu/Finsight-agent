"""Generate mock credit card metrics data into SQLite.

Run: python scripts/seed_data.py [--db-path ./data/finsight.db]
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import numpy as np


REGIONS = ["华东", "华南", "华北", "华西", "华中"]
MONTHS = [f"2025-{m:02d}" for m in range(4, 13)] + [f"2026-{m:02d}" for m in range(1, 4)]

SCHEMA = """
CREATE TABLE credit_card_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year_month TEXT NOT NULL,
    region TEXT NOT NULL,
    new_customers INTEGER NOT NULL,
    activation_rate REAL NOT NULL,
    monthly_transaction_volume REAL NOT NULL,
    overdue_rate REAL NOT NULL,
    collection_recovery_rate REAL NOT NULL,
    customer_complaints INTEGER NOT NULL,
    revenue_per_customer REAL NOT NULL,
    churn_rate REAL NOT NULL,
    UNIQUE(year_month, region)
);
CREATE INDEX idx_region_month ON credit_card_metrics(region, year_month);
"""

BASELINES = {
    "华东": {"new": 2800, "act": 0.78, "vol": 2200, "ovr": 0.032, "col": 0.86, "cpl": 120, "rpc": 680, "chn": 0.028},
    "华南": {"new": 2600, "act": 0.76, "vol": 1950, "ovr": 0.034, "col": 0.84, "cpl": 130, "rpc": 650, "chn": 0.030},
    "华北": {"new": 2400, "act": 0.80, "vol": 1800, "ovr": 0.030, "col": 0.87, "cpl": 110, "rpc": 700, "chn": 0.025},
    "华西": {"new": 1800, "act": 0.74, "vol": 1400, "ovr": 0.036, "col": 0.83, "cpl": 140, "rpc": 600, "chn": 0.032},
    "华中": {"new": 2000, "act": 0.77, "vol": 1600, "ovr": 0.033, "col": 0.85, "cpl": 125, "rpc": 640, "chn": 0.029},
}


def generate_row(region: str, month: str, rng: np.random.Generator) -> tuple:
    b = BASELINES[region]
    new_c = int(rng.normal(b["new"], b["new"] * 0.06))
    act = float(np.clip(rng.normal(b["act"], 0.015), 0.6, 0.9))
    vol = float(rng.normal(b["vol"], b["vol"] * 0.08))
    ovr = float(np.clip(rng.normal(b["ovr"], 0.002), 0.02, 0.045))
    col = float(np.clip(rng.normal(b["col"], 0.015), 0.75, 0.95))
    cpl = int(rng.normal(b["cpl"], 12))
    rpc = float(rng.normal(b["rpc"], 25))
    chn = float(np.clip(rng.normal(b["chn"], 0.003), 0.015, 0.05))
    return (month, region, new_c, act, round(vol, 2), round(ovr, 4), round(col, 4), cpl, round(rpc, 2), round(chn, 4))


def apply_anomalies(rows: list[tuple]) -> list[tuple]:
    """Inject engineered anomalies into the dataset."""
    result = []
    for row in rows:
        month, region, new_c, act, vol, ovr, col, cpl, rpc, chn = row
        # 华东 2026-03 逾期率飙升 + 投诉量 +40% + 催收率 -5%
        if region == "华东" and month == "2026-03":
            ovr = 0.058
            cpl = int(cpl * 1.4)
            col = round(col - 0.05, 4)
        # 华南 2026-02 获客 1800, 2026-03 获客 1450 + 激活率同步走低
        if region == "华南" and month == "2026-02":
            new_c = 1800
            act = round(act - 0.04, 4)
        if region == "华南" and month == "2026-03":
            new_c = 1450
            act = round(act - 0.06, 4)
        result.append((month, region, new_c, act, vol, ovr, col, cpl, rpc, chn))
    return result


def seed(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    rng = np.random.default_rng(seed=42)
    rows = [generate_row(r, m, rng) for r in REGIONS for m in MONTHS]
    rows = apply_anomalies(rows)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT INTO credit_card_metrics "
            "(year_month, region, new_customers, activation_rate, monthly_transaction_volume, "
            " overdue_rate, collection_recovery_rate, customer_complaints, "
            " revenue_per_customer, churn_rate) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            rows,
        )
        conn.commit()
        print(f"Seeded {len(rows)} rows into {db_path}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default="./data/finsight.db")
    args = parser.parse_args()
    seed(Path(args.db_path))


if __name__ == "__main__":
    main()
