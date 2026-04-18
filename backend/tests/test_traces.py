"""Tests for trace persistence + API."""
import pytest
from fastapi.testclient import TestClient

from backend.agent.models import TraceLog, TraceStep
from backend.db.database import execute
from backend.db.traces import (
    delete_trace,
    get_trace_detail,
    list_traces,
    save_trace,
)
from backend.main import app


@pytest.fixture(autouse=True)
def clean_tables():
    execute("DELETE FROM trace_steps", ())
    execute("DELETE FROM traces", ())
    yield
    execute("DELETE FROM trace_steps", ())
    execute("DELETE FROM traces", ())


def _make_trace(trace_id: str = "trace-test-001") -> TraceLog:
    return TraceLog(
        trace_id=trace_id,
        user_query="测试查询",
        llm_model="test-model",
        status="success",
        total_latency_ms=1500,
        steps=[
            TraceStep(step_number=0, action_type="llm_reasoning",
                      tool_output_summary="思考:我需要..."),
            TraceStep(step_number=0, action_type="tool_call",
                      tool_name="anomaly_detect",
                      tool_input={"metric": "overdue_rate"},
                      tool_output_summary="✅ 检测完成",
                      latency_ms=200),
        ],
    )


def test_save_and_list():
    save_trace(_make_trace("trace-a"))
    items = list_traces()
    assert len(items) == 1
    assert items[0]["trace_id"] == "trace-a"
    assert items[0]["status"] == "success"
    assert items[0]["step_count"] == 2


def test_list_ordering_newest_first():
    save_trace(_make_trace("trace-older"), started_at="2026-03-01T00:00:00Z")
    save_trace(_make_trace("trace-newer"), started_at="2026-04-01T00:00:00Z")
    items = list_traces()
    assert items[0]["trace_id"] == "trace-newer"
    assert items[1]["trace_id"] == "trace-older"


def test_get_detail_includes_steps():
    save_trace(_make_trace("trace-d"))
    detail = get_trace_detail("trace-d")
    assert detail is not None
    assert len(detail["steps"]) == 2
    # Second step should have parsed JSON tool_input
    second = detail["steps"][1]
    assert second["tool_name"] == "anomaly_detect"
    assert second["tool_input"] == {"metric": "overdue_rate"}


def test_upsert_replaces_steps():
    trace = _make_trace("trace-u")
    save_trace(trace)
    # Modify and save again with fewer steps
    trace.steps = trace.steps[:1]
    save_trace(trace)
    detail = get_trace_detail("trace-u")
    assert detail is not None
    assert len(detail["steps"]) == 1  # replaced, not appended


def test_delete_trace():
    save_trace(_make_trace("trace-del"))
    assert delete_trace("trace-del") is True
    assert get_trace_detail("trace-del") is None
    assert delete_trace("trace-del") is False


# --- API tests ---

@pytest.fixture
def client():
    return TestClient(app)


def test_api_list_empty(client):
    resp = client.get("/api/traces")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["traces"] == []


def test_api_list_after_save(client):
    save_trace(_make_trace("trace-api-1"))
    resp = client.get("/api/traces")
    assert resp.json()["count"] == 1


def test_api_detail_404(client):
    resp = client.get("/api/traces/nonexistent")
    assert resp.status_code == 404


def test_api_detail_200(client):
    save_trace(_make_trace("trace-api-2"))
    resp = client.get("/api/traces/trace-api-2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["trace_id"] == "trace-api-2"
    assert len(body["steps"]) == 2


def test_api_delete(client):
    save_trace(_make_trace("trace-api-d"))
    resp = client.delete("/api/traces/trace-api-d")
    assert resp.json()["deleted"] is True
    assert client.get("/api/traces/trace-api-d").status_code == 404
