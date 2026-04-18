"""Tests for HITL approvals persistence + API."""
import pytest
from fastapi.testclient import TestClient

from backend.db.approvals import (
    get_decision,
    revoke_decision,
    submit_decision,
)
from backend.db.database import execute
from backend.main import app


@pytest.fixture(autouse=True)
def clean_approvals():
    """Wipe approvals table before each test so runs are isolated."""
    execute("DELETE FROM approvals", ())
    yield
    execute("DELETE FROM approvals", ())


def test_submit_and_get_decision():
    submit_decision("rpt-001", "approved", trace_id="trace-abc", decided_by="ops1")
    got = get_decision("rpt-001")
    assert got is not None
    assert got["decision"] == "approved"
    assert got["trace_id"] == "trace-abc"
    assert got["decided_by"] == "ops1"
    assert got["decided_at"].endswith("Z")


def test_get_missing_returns_none():
    assert get_decision("rpt-nope") is None


def test_submit_rejected():
    submit_decision("rpt-002", "rejected", note="指标偏差过大")
    got = get_decision("rpt-002")
    assert got["decision"] == "rejected"
    assert got["note"] == "指标偏差过大"


def test_upsert_overrides():
    submit_decision("rpt-003", "approved")
    submit_decision("rpt-003", "rejected", note="重新审批")
    got = get_decision("rpt-003")
    assert got["decision"] == "rejected"
    assert got["note"] == "重新审批"


def test_invalid_decision_raises():
    with pytest.raises(ValueError):
        submit_decision("rpt-004", "maybe")  # type: ignore[arg-type]


def test_revoke():
    submit_decision("rpt-005", "approved")
    assert revoke_decision("rpt-005") is True
    assert get_decision("rpt-005") is None
    assert revoke_decision("rpt-005") is False


# --- API tests ---

@pytest.fixture
def client():
    return TestClient(app)


def test_api_post_approve(client):
    resp = client.post("/api/approve/rpt-api-1", json={"decision": "approved"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "approved"
    assert body["report_id"] == "rpt-api-1"


def test_api_get_pending(client):
    resp = client.get("/api/approve/rpt-unknown")
    assert resp.status_code == 200
    assert resp.json()["decision"] is None


def test_api_get_after_submit(client):
    client.post(
        "/api/approve/rpt-api-2",
        json={"decision": "rejected", "note": "数据来源不可靠"},
    )
    resp = client.get("/api/approve/rpt-api-2")
    assert resp.json()["decision"] == "rejected"
    assert resp.json()["note"] == "数据来源不可靠"


def test_api_invalid_decision_rejected(client):
    resp = client.post("/api/approve/rpt-bad", json={"decision": "maybe"})
    assert resp.status_code == 422  # pydantic Literal validation


def test_api_delete_revokes(client):
    client.post("/api/approve/rpt-del", json={"decision": "approved"})
    resp = client.delete("/api/approve/rpt-del")
    assert resp.json()["revoked"] is True
    # And subsequent GET shows pending
    resp = client.get("/api/approve/rpt-del")
    assert resp.json()["decision"] is None
