import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from fastapi import HTTPException

from typing import Literal

from .agent.orchestrator import run_agent
from .config import settings
from .db.approvals import get_decision, revoke_decision, submit_decision
from .db.kpi import aggregate_kpi
from .db.traces import delete_trace, get_trace_detail, list_traces
from .knowledge_base.loader import get_case, load_all_cases

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
    return {"status": "ok", "model": settings.llm_model, "provider": settings.llm_provider}


@app.get("/api/kpi")
async def kpi() -> dict:
    """Live KPI aggregation from credit_card_metrics + industry_benchmark.
    Latest month is aggregated across all regions; change% is vs previous month;
    alert flags are driven by the industry_benchmark table's direction field."""
    return aggregate_kpi()


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


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest) -> StreamingResponse:
    async def stream():
        async for event in run_agent(req.query):
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
