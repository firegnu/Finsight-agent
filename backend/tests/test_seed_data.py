import sqlite3
import subprocess
from pathlib import Path

import pytest


DB_PATH = Path("data/finsight_test.db")


@pytest.fixture(scope="module")
def seeded_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    subprocess.run(
        ["python", "scripts/seed_data.py", "--db-path", str(DB_PATH)],
        check=True,
    )
    conn = sqlite3.connect(DB_PATH)
    yield conn
    conn.close()
    if DB_PATH.exists():
        DB_PATH.unlink()


def test_row_count_is_60(seeded_db):
    cursor = seeded_db.execute("SELECT COUNT(*) FROM credit_card_metrics")
    assert cursor.fetchone()[0] == 60


def test_regions_are_five(seeded_db):
    cursor = seeded_db.execute("SELECT DISTINCT region FROM credit_card_metrics")
    regions = {row[0] for row in cursor.fetchall()}
    assert regions == {"华东", "华南", "华北", "华西", "华中"}


def test_east_march_overdue_spike(seeded_db):
    cursor = seeded_db.execute(
        "SELECT overdue_rate FROM credit_card_metrics WHERE region=? AND year_month=?",
        ("华东", "2026-03"),
    )
    overdue = cursor.fetchone()[0]
    assert 0.055 <= overdue <= 0.060, f"Expected ~5.8%, got {overdue}"


def test_south_feb_mar_new_customers_drop(seeded_db):
    cursor = seeded_db.execute(
        "SELECT new_customers FROM credit_card_metrics WHERE region=? AND year_month IN (?, ?)",
        ("华南", "2026-02", "2026-03"),
    )
    values = [row[0] for row in cursor.fetchall()]
    assert all(v < 2000 for v in values), f"Expected <2000, got {values}"


def test_other_regions_overdue_normal(seeded_db):
    cursor = seeded_db.execute(
        "SELECT region, year_month, overdue_rate FROM credit_card_metrics "
        "WHERE region != '华东' AND year_month = '2026-03'"
    )
    for region, month, ovr in cursor.fetchall():
        assert 0.02 <= ovr <= 0.045, f"{region} {month} overdue {ovr} out of normal range"
