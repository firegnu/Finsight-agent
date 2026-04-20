"""Tests for multi-provider config, factory, and API endpoints."""
import pytest
from fastapi.testclient import TestClient

from backend.config import Settings, settings
from backend.llm.client import get_client
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ---- config.Settings.providers ----

def test_providers_list_includes_configured_ids():
    """Both LM Studio + Zhipu should load when both are configured in .env."""
    ids = [p.id for p in settings.providers]
    assert "lmstudio" in ids
    assert "zhipu" in ids


def test_providers_list_skips_empty_api_key():
    """A provider with blank api_key is omitted from the registry."""
    s = Settings(
        default_provider_id="lmstudio",
        lmstudio_base_url="http://x/v1",
        lmstudio_api_key="lm-studio",
        lmstudio_model="m1",
        zhipu_base_url="https://y/v1",
        zhipu_api_key="",
        zhipu_model="m2",
    )
    ids = [p.id for p in s.providers]
    assert "lmstudio" in ids
    assert "zhipu" not in ids


def test_get_provider_returns_default_when_none():
    p = settings.get_provider(None)
    assert p.id == settings.default_provider_id


def test_get_provider_raises_on_unknown():
    with pytest.raises(KeyError):
        settings.get_provider("does-not-exist")


# ---- llm.client.get_client ----

def test_get_client_returns_bundle():
    bundle = get_client("lmstudio")
    assert bundle.provider_id == "lmstudio"
    assert bundle.model == settings.get_provider("lmstudio").model
    assert bundle.client is not None


def test_get_client_caches_on_url_and_key():
    """Same (base_url, api_key) should reuse the same AsyncOpenAI instance."""
    b1 = get_client("lmstudio")
    b2 = get_client("lmstudio")
    assert b1.client is b2.client


def test_get_client_different_providers_get_different_clients():
    lm = get_client("lmstudio")
    zp = get_client("zhipu")
    assert lm.client is not zp.client
    assert lm.provider_id != zp.provider_id


def test_get_client_defaults_to_configured_default():
    bundle = get_client(None)
    assert bundle.provider_id == settings.default_provider_id


# ---- /api/providers endpoint ----

def test_api_providers_returns_registered(client):
    resp = client.get("/api/providers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["default_provider_id"] == settings.default_provider_id
    ids = [p["id"] for p in body["providers"]]
    assert set(ids) == {"lmstudio", "zhipu", "deepseek"}
    # Exactly one provider is flagged default
    assert sum(1 for p in body["providers"] if p["default"]) == 1


def test_api_providers_item_shape(client):
    body = client.get("/api/providers").json()
    item = body["providers"][0]
    assert set(item.keys()) == {"id", "label", "model", "default"}


# ---- /api/health with default provider ----

def test_api_health_reports_default_provider(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["provider"] == settings.default_provider_id


# ---- /api/analyze validation ----

def test_analyze_rejects_unknown_provider_id(client):
    resp = client.post(
        "/api/analyze",
        json={"query": "test", "provider_id": "nonexistent"},
    )
    assert resp.status_code == 400
    assert "nonexistent" in resp.json()["detail"]
