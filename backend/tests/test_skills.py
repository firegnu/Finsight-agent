"""Tests for skills loader + use_skill tool + API."""
import asyncio

from fastapi.testclient import TestClient

from backend.main import app
from backend.skills.loader import get_skill, list_skill_names, load_all_skills
from backend.tools.use_skill import TOOL_SCHEMA, run


def test_load_all_skills_returns_five():
    skills = load_all_skills()
    assert len(skills) == 5
    names = {s["name"] for s in skills}
    assert names == {
        "acquisition-diagnosis",
        "anomaly-investigation",
        "churn-early-warning",
        "cross-region-comparison",
        "executive-briefing",
    }


def test_each_skill_has_required_fields():
    for s in load_all_skills():
        assert s["name"]
        assert s["description"]
        assert s["category"]
        assert s["content"]
        assert isinstance(s["applicable_metrics"], list)


def test_get_skill_by_name():
    s = get_skill("anomaly-investigation")
    assert s is not None
    assert "四步" in s["content"] or "Step" in s["content"]


def test_get_unknown_skill_returns_none():
    assert get_skill("nonexistent") is None


def test_tool_schema_enum_matches_skills():
    names_in_enum = TOOL_SCHEMA["function"]["parameters"]["properties"]["skill_name"]["enum"]
    assert set(names_in_enum) == set(list_skill_names())


def test_run_returns_skill_content():
    result = asyncio.run(run("anomaly-investigation"))
    assert "error" not in result
    assert result["name"] == "anomaly-investigation"
    assert result["content"]
    assert result["category"] == "methodology"


def test_run_unknown_returns_error():
    result = asyncio.run(run("bogus-name"))
    assert "error" in result


# --- API tests ---

def test_api_list_skills():
    client = TestClient(app)
    resp = client.get("/api/skills")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 5
    assert len(body["skills"]) == 5
    # snippet should be present but content should not (to keep list response small)
    sample = body["skills"][0]
    assert sample["snippet"]
    assert "content" not in sample


def test_api_get_skill_detail():
    client = TestClient(app)
    resp = client.get("/api/skills/executive-briefing")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "executive-briefing"
    assert body["category"] == "communication"
    assert body["content"]


def test_api_get_skill_404():
    client = TestClient(app)
    resp = client.get("/api/skills/nope")
    assert resp.status_code == 404


def test_system_prompt_includes_skills_catalog():
    from backend.agent.prompts import SYSTEM_PROMPT

    for name in list_skill_names():
        assert name in SYSTEM_PROMPT, f"skill '{name}' missing from SYSTEM_PROMPT"
