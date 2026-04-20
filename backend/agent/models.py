from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class AnomalyFinding(BaseModel):
    metric: str
    region: str
    period: str
    current_value: float
    historical_mean: float
    historical_std: float
    deviation_sigma: float
    baseline_value: float | None = None
    severity: Literal["low", "medium", "high", "critical"]
    root_cause_hypothesis: str = ""
    references: list[str] = []


class ActionItem(BaseModel):
    title: str
    description: str
    priority: Literal["P0", "P1", "P2", "P3"]
    expected_impact: str
    owner_suggestion: str
    deadline_suggestion: str


class AnalysisReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"rpt-{uuid4().hex[:8]}")
    trace_id: str = Field(default_factory=lambda: f"trace-{uuid4().hex[:12]}")
    generated_at: str = Field(default_factory=_utc_iso)
    period: str
    executive_summary: str
    key_findings: list[str]
    anomalies: list[AnomalyFinding]
    action_items: list[ActionItem]
    data_sources: list[str]
    requires_human_review: bool = False


class TraceStep(BaseModel):
    step_number: int
    action_type: Literal["llm_reasoning", "tool_call", "tool_result", "tool_error"]
    tool_name: str | None = None
    tool_input: dict | None = None
    tool_output_summary: str | None = None
    latency_ms: int = 0
    timestamp: str = Field(default_factory=_utc_iso)


class TraceLog(BaseModel):
    trace_id: str
    user_query: str
    steps: list[TraceStep] = []
    final_report: AnalysisReport | None = None
    total_latency_ms: int = 0
    llm_model: str
    provider_id: str = "unknown"
    status: Literal["success", "error", "running"] = "running"
