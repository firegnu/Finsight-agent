"""Tests for rag_search tool. Assumes Chroma collection is already built
by scripts/index_cases.py and LM Studio embedding endpoint is available."""
import asyncio
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="module", autouse=True)
def ensure_index():
    """Rebuild the Chroma collection once before running RAG tests so
    results are deterministic vs whatever may be on disk."""
    subprocess.run(
        [sys.executable, "scripts/index_cases.py"],
        check=True,
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True,
    )


def test_overdue_query_hits_east_case():
    from backend.tools.rag_search import run

    result = asyncio.run(run(
        "华东区逾期率飙升的根因", metric="overdue_rate",
    ))
    assert result["hit_count"] >= 1
    ids = [h["id"] for h in result["hits"]]
    # The east overdue spike case should appear in the top results when
    # filtering by metric=overdue_rate.
    assert "east-2024-q3-overdue-spike" in ids


def test_churn_query_hits_churn_methodology():
    from backend.tools.rag_search import run

    result = asyncio.run(run(
        "客户流失有哪些早期信号", metric="churn_rate",
    ))
    assert result["hit_count"] >= 1
    assert result["hits"][0]["id"] == "method-churn-early-warning"


def test_hits_include_score_and_snippet():
    from backend.tools.rag_search import run

    result = asyncio.run(run("获客量下滑怎么调查", metric="new_customers"))
    assert result["hit_count"] >= 1
    top = result["hits"][0]
    assert 0 <= top["score"] <= 1
    assert top["snippet"]
    assert top["title"]
    assert isinstance(top["tags"], list)


def test_empty_query_returns_error():
    from backend.tools.rag_search import run

    result = asyncio.run(run("   "))
    assert "error" in result


def test_unknown_metric_falls_back():
    """Unknown metric value → Chroma where filter matches 0 docs → fallback to no filter."""
    from backend.tools.rag_search import run

    result = asyncio.run(run("异常调查", metric="nonexistent_metric_xyz"))
    # Should still return hits via fallback (all cases eligible without filter)
    assert result["hit_count"] >= 1
