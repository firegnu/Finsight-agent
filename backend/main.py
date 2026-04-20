import logging
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from .agent.orchestrator import run_agent
from .config import settings
from .db.approvals import get_decision, revoke_decision, submit_decision
from .db.kpi import aggregate_kpi
from .db.traces import delete_trace, get_trace_detail, list_traces
from .knowledge_base.loader import get_case, load_all_cases
from .skills.loader import get_skill, load_all_skills

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("finsight")

app = FastAPI(title="FinSight Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    try:
        default = settings.get_provider(None)
        return {
            "status": "ok",
            "model": default.model,
            "provider": default.id,
            "default_provider_id": default.id,
        }
    except KeyError as e:
        return {"status": "degraded", "error": str(e)}


@app.get("/api/providers")
async def list_providers() -> dict:
    """Return configured chat providers (the embedding provider is
    deliberately not switchable, so it's excluded here)."""
    default_id = settings.default_provider_id
    return {
        "default_provider_id": default_id,
        "providers": [
            {
                "id": p.id,
                "label": p.label,
                "model": p.model,
                "default": p.id == default_id,
            }
            for p in settings.providers
        ],
    }


@app.get("/api/kpi")
async def kpi() -> dict:
    """Live KPI aggregation from credit_card_metrics + industry_benchmark.
    Latest month is aggregated across all regions; change% is vs previous month;
    alert flags are driven by the industry_benchmark table's direction field."""
    return aggregate_kpi()


@app.get("/api/skills")
async def list_skills() -> dict:
    """Return all available methodology skills (metadata + snippet of content)."""
    skills = load_all_skills()
    return {
        "count": len(skills),
        "skills": [
            {
                "name": s["name"],
                "description": s["description"],
                "category": s["category"],
                "applicable_metrics": s["applicable_metrics"],
                "source_file": s["source_file"],
                "snippet": _skill_snippet(s["content"]),
            }
            for s in skills
        ],
    }


@app.get("/api/skills/{name}")
async def get_skill_detail(name: str) -> dict:
    """Return a single skill with full markdown content."""
    skill = get_skill(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"skill not found: {name}")
    return skill


def _skill_snippet(content: str, n: int = 220) -> str:
    lines = [l for l in content.split("\n") if l.strip() and not l.startswith("#")]
    text = " ".join(lines[:5])
    compact = " ".join(text.split())
    return compact[:n] + ("…" if len(compact) > n else "")


@app.get("/api/cases")
async def list_cases() -> dict:
    """Return all historical cases (metadata + snippet, no full content).
    Frontend uses this for id→title mapping in AnomalyCard references."""
    cases = load_all_cases()
    return {
        "count": len(cases),
        "cases": [
            {k: v for k, v in c.items() if k != "content"}
            for c in cases
        ],
    }


@app.get("/api/cases/{case_id}")
async def get_case_detail(case_id: str) -> dict:
    """Return a single case with full markdown content. Used for
    AnomalyCard click-to-expand in the UI."""
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"case not found: {case_id}")
    return case


class ApprovalRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    trace_id: str | None = None
    decided_by: str | None = None
    note: str | None = None


@app.post("/api/approve/{report_id}")
async def approve_report(report_id: str, req: ApprovalRequest) -> dict:
    """Record a HITL approval decision for a report. Upsert: the latest
    POST for a report_id overrides prior decisions."""
    return submit_decision(
        report_id=report_id,
        decision=req.decision,
        trace_id=req.trace_id,
        decided_by=req.decided_by,
        note=req.note,
    )


@app.get("/api/approve/{report_id}")
async def get_approval(report_id: str) -> dict:
    """Return the current approval decision for a report, or status='pending'
    when no decision has been recorded yet."""
    decision = get_decision(report_id)
    if not decision:
        return {"report_id": report_id, "decision": None}
    return decision


@app.delete("/api/approve/{report_id}")
async def revoke_approval(report_id: str) -> dict:
    """Delete a recorded approval (allow the report to return to pending)."""
    removed = revoke_decision(report_id)
    return {"report_id": report_id, "revoked": removed}


@app.get("/api/traces")
async def traces_list(limit: int = 50) -> dict:
    """Return recent analysis traces (newest first). Each trace includes
    summary metadata but not individual steps — call /api/traces/{id} for detail."""
    items = list_traces(limit=limit)
    return {"count": len(items), "traces": items}


@app.get("/api/traces/{trace_id}")
async def trace_detail(trace_id: str) -> dict:
    """Return a single trace with all steps + final report JSON."""
    detail = get_trace_detail(trace_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"trace not found: {trace_id}")
    return detail


@app.delete("/api/traces/{trace_id}")
async def trace_delete(trace_id: str) -> dict:
    removed = delete_trace(trace_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"trace not found: {trace_id}")
    return {"trace_id": trace_id, "deleted": True}


class AnalyzeRequest(BaseModel):
    query: str
    provider_id: str | None = None


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest) -> StreamingResponse:
    if req.provider_id is not None:
        try:
            settings.get_provider(req.provider_id)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def stream():
        async for event in run_agent(req.query, provider_id=req.provider_id):
            yield event.serialize()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Frontend static hosting (production single-process mode)
#
# When `frontend/dist` exists (after `make build`), this mount serves the SPA
# at the same origin as the API — no CORS, one port, one process. In dev the
# directory is absent and this block no-ops, so `make dev-backend` +
# `make dev-frontend` still works as before (Vite @ :5173 proxying to :8000).
# ---------------------------------------------------------------------------

_DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if _DIST_DIR.is_dir() and (_DIST_DIR / "index.html").is_file():
    logger.info("serving frontend build from %s", _DIST_DIR)

    # Catch-all for any non-API path: serve the real file if it exists
    # (/, /favicon.svg, /assets/*.js, etc.), else fall back to index.html
    # so SPA deep links / refreshes don't 404. Registered AFTER all /api/*
    # routes above so FastAPI matches those first.
    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        asset = _DIST_DIR / full_path
        if asset.is_file():
            return FileResponse(asset)
        return FileResponse(_DIST_DIR / "index.html")
else:
    logger.info(
        "frontend/dist not found at %s — dev mode (API only). "
        "Run `make build` for single-process production mode.",
        _DIST_DIR,
    )
