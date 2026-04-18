// Aligned with backend/agent/models.py (Pydantic) and backend/sse/events.py.

export type EventType =
  | "start"
  | "thinking"
  | "tool_call"
  | "tool_result"
  | "tool_error"
  | "final_text"
  | "report"
  | "done"
  | "error";

export interface SSEEvent {
  type: EventType;
  data: Record<string, unknown>;
}

export type Severity = "low" | "medium" | "high" | "critical";
export type Priority = "P0" | "P1" | "P2" | "P3";

export interface AnomalyFinding {
  metric: string;
  region: string;
  period: string;
  current_value: number;
  historical_mean: number;
  historical_std: number;
  deviation_sigma: number;
  baseline_value: number | null;
  severity: Severity;
  root_cause_hypothesis: string;
  references: string[];
}

export interface ActionItem {
  title: string;
  description: string;
  priority: Priority;
  expected_impact: string;
  owner_suggestion: string;
  deadline_suggestion: string;
}

export interface AnalysisReport {
  report_id: string;
  trace_id: string;
  generated_at: string;
  period: string;
  executive_summary: string;
  key_findings: string[];
  anomalies: AnomalyFinding[];
  action_items: ActionItem[];
  data_sources: string[];
  requires_human_review: boolean;
}

export interface KPIMetric {
  name: string;
  value: string;
  change: string;
  trend: "up" | "down" | "flat";
  alert: boolean;
}

export interface KPIResponse {
  period: string;
  updated_at: string;
  metrics: KPIMetric[];
}

export interface HealthResponse {
  status: string;
  model: string;
  provider: string;
}

export type AgentStatus = "idle" | "running" | "done" | "error";

// RAG case library
export interface CaseMeta {
  id: string;
  title: string;
  tags: string[];
  region: string;
  metric: string;
  period: string;
  severity: string;
  source_file: string;
  snippet: string;
}

export interface CaseDetail extends CaseMeta {
  content: string;
}

export interface CasesResponse {
  count: number;
  cases: CaseMeta[];
}

// A single rag_search hit embedded in the tool_result SSE event
export interface RagHit {
  id: string;
  title: string;
  tags: string[];
  region: string;
  metric: string;
  period: string;
  score: number;
  snippet: string;
}

// HITL approval
export type ApprovalDecision = "approved" | "rejected";

export interface ApprovalRecord {
  report_id: string;
  trace_id: string | null;
  decision: ApprovalDecision | null;
  decided_by: string | null;
  note: string | null;
  decided_at?: string;
}
